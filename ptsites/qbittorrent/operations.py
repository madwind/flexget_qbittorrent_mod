from __future__ import annotations

import math
import os
import re

from flexget import plugin
from flexget.task import Task
from loguru import logger

from ..utils import net_utils


class QBittorrentOperationsMixin:
    def add_entries(self, task: Task, add_options: dict) -> None:
        add_option_str_list = ['savepath',
                               'cookie',
                               'category',
                               'tags',
                               'skip_checking',
                               'paused',
                               'root_folder',
                               'rename',
                               'upLimit',
                               'dlLimit',
                               'autoTMM',
                               'sequentialDownload',
                               'firstLastPiecePrio']
        for entry in task.accepted:
            is_magnet = entry['url'].startswith('magnet:')
            entry_add_option = add_options.copy()
            if not is_magnet and (tracker_options := add_options.get('tracker_options')):
                tags = []
                if 'torrent' in entry:
                    torrent = entry['torrent']
                    trackers = torrent.trackers
                    for tracker in trackers:
                        site_name = net_utils.get_site_name(tracker)
                        tags.append(site_name)
                        if specific_trackers := tracker_options.get('specific_trackers'):
                            for specific_tracker in specific_trackers:
                                for tracker_name, tracker_option in specific_tracker.items():
                                    if tracker_name == site_name:
                                        net_utils.dict_merge(entry_add_option, tracker_option)
                    if tracker_options.get('tag_by_tracker'):
                        if original_tags := entry_add_option.get('tags'):
                            tags.append(original_tags)
                        entry_add_option['tags'] = ','.join(set(tags))

            options = {}

            for attr_str in add_option_str_list:
                entry_attr = entry.get(attr_str)
                add_options_attr = entry_add_option.get(attr_str)
                if attr_str == 'tags' and entry_attr and add_options_attr:
                    attr = ','.join([entry_attr, add_options_attr])
                else:
                    attr = entry_attr if entry_attr is not None else add_options_attr
                if attr is not None:
                    options[attr_str] = attr

            if options.get('autoTMM') and options.get('category') and options.get('savepath'):
                del options['savepath']

            logger.debug(f"url: {entry['url']}, options: {options}")

            if not is_magnet:
                if 'file' not in entry:
                    entry.fail('File missing?')
                    return
                if not os.path.exists(entry['file']):
                    tmp_path = os.path.join(task.manager.config_base, 'temp')
                    logger.debug('entry: {}', entry)
                    logger.debug('temp: {}', ', '.join(os.listdir(tmp_path)))
                    entry.fail("Downloaded temp file '%s' doesn't exist!?" % entry['file'])
                    return
                self.client.add_torrent_file(entry['file'], options)
            else:
                self.client.add_torrent_url(entry['url'], options)

    def remove_entries(self, task: Task, remove_options: dict) -> None:
        (mode_name, option), = remove_options.items()
        mode = getattr(self, 'remove_entries_' + mode_name, None)
        if mode:
            mode(task, option)
        else:
            raise plugin.PluginError('Unknown mode.')

    def remove_entries_keeper(self, task: Task, keeper_options: dict) -> None:
        delete_files = keeper_options.get('delete_files')
        check_reseed = keeper_options.get('check_reseed')
        keep_disk_space = keeper_options.get('keep_disk_space')

        dl_limit_interval = keeper_options.get('dl_limit_interval', 24 * 60 * 60)
        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        server_state = main_data_snapshot.get('server_state')

        dl_rate_limit = server_state.get('dl_rate_limit')
        free_space_on_disk = server_state.get('free_space_on_disk')

        dl_limit_mode = 'dl_limit'
        dl_limit_on_succeeded = keeper_options.get('dl_limit_on_succeeded', 0)
        alt_dl_limit_on_succeeded = keeper_options.get('alt_dl_limit_on_succeeded', 0)
        if server_state.get('use_alt_speed_limits'):
            dl_limit_mode = 'alt_dl_limit'
            dl_limit_on_succeeded = alt_dl_limit_on_succeeded

        keep_disk_space = keep_disk_space * 1024 * 1024 * 1024
        if keep_disk_space < free_space_on_disk:
            if dl_limit_on_succeeded is not None:
                dl_limit = math.floor(dl_limit_on_succeeded / 1024) * 1024
                if dl_limit != dl_rate_limit:
                    self.client.set_application_preferences('{{"{}": {}}}'.format(dl_limit_mode, dl_limit))
                    logger.info("set {} to {} KiB/s", dl_limit_mode, dl_limit / 1024)
            for entry in task.accepted:
                entry.reject(reason='keep_disk_space < free_space_on_disk')
            return

        accepted_entry_hashes = []
        delete_hashes = []

        delete_size = 0

        if not task.accepted:
            self.calc_and_set_dl_limit(keep_disk_space, free_space_on_disk, delete_size, dl_limit_interval,
                                       dl_limit_on_succeeded, dl_rate_limit, dl_limit_mode)
            return

        entry_dict = main_data_snapshot.get('entry_dict')
        reseed_dict = main_data_snapshot.get('reseed_dict')
        for entry in task.accepted:
            accepted_entry_hashes.append(entry['torrent_info_hash'])

        for entry_hash in accepted_entry_hashes:
            if entry_hash in delete_hashes:
                continue
            if keep_disk_space < free_space_on_disk + delete_size:
                entry_dict.get(entry_hash).reject(reason='keep_disk_space < free_space_on_disk')
                continue
            if not (server_entry := entry_dict.get(entry_hash)):
                self.client.reset_rid()
            save_path_with_name = server_entry.get('qbittorrent_save_path_with_name')
            reseed_entry_list = reseed_dict.get(save_path_with_name)
            check_hashes = []
            torrent_hashes = []
            torrent_size = 0

            for reseed_entry in reseed_entry_list:
                if reseed_entry['qbittorrent_completed'] != 0:
                    torrent_size = reseed_entry['qbittorrent_completed']
                if isinstance(check_reseed, list):
                    site_names = []
                    for tracker in reseed_entry['qbittorrent_trackers']:
                        site_names.append(net_utils.get_site_name(tracker.get('url')))

                    if len(set(check_reseed) & set(site_names)) > 0:
                        check_hashes.append(reseed_entry['torrent_info_hash'])
                else:
                    check_hashes.append(reseed_entry['torrent_info_hash'])
                torrent_hashes.append(reseed_entry['torrent_info_hash'])
            if check_reseed and not set(accepted_entry_hashes) >= set(check_hashes):
                for torrent_hash in torrent_hashes:
                    entry_dict.get(torrent_hash).reject(
                        reason='torrents with the same save path are not all tested')
                continue
            elif keep_disk_space > free_space_on_disk + delete_size:
                delete_size += torrent_size
                self._build_delete_hashes(delete_hashes, torrent_hashes, entry_dict, keep_disk_space,
                                          free_space_on_disk, delete_size)

        self.calc_and_set_dl_limit(keep_disk_space, free_space_on_disk, delete_size, dl_limit_interval,
                                   dl_limit_on_succeeded, dl_rate_limit, dl_limit_mode)
        if len(delete_hashes) > 0:
            self.client.delete_torrents('|'.join(delete_hashes), delete_files)

    def calc_and_set_dl_limit(self, keep_disk_space, free_space_on_disk, delete_size, dl_limit_interval,
                              dl_limit_on_succeeded, dl_rate_limit, dl_limit_mode):
        if keep_disk_space > free_space_on_disk + delete_size:
            dl_limit = (free_space_on_disk + delete_size) / dl_limit_interval
            if dl_limit_on_succeeded and dl_limit > dl_limit_on_succeeded:
                dl_limit = dl_limit_on_succeeded
            dl_limit = math.floor(dl_limit / 1024) * 1024
            if dl_limit != dl_rate_limit:
                self.client.set_application_preferences('{{"{}": {}}}'.format(dl_limit_mode, dl_limit))
                logger.warning("not enough disk space, set {} to {} KiB/s", dl_limit_mode, dl_limit / 1024)

    def _build_delete_hashes(self, delete_hashes, torrent_hashes, all_entry_map, keep_disk_space, free_space_on_disk,
                             delete_size):
        delete_hashes.extend(torrent_hashes)
        logger.info('keep_disk_space: {:.2F} GiB, free_space_on_disk: {:.2f} GiB, delete_size: {:.2f} GiB',
                    keep_disk_space / (1024 * 1024 * 1024), free_space_on_disk / (1024 * 1024 * 1024),
                    delete_size / (1024 * 1024 * 1024))
        entries = []
        for torrent_hash in torrent_hashes:
            entry = all_entry_map.get(torrent_hash)
            entry.accept(reason='torrent with the same save path are all pass tested')
            entries.append(entry)
        entries.sort(key=lambda e: e['qbittorrent_last_activity'], reverse=True)

        for entry in entries:
            logger.info(
                '{}, size: {:.2f} GiB, seeding_time: {:.2f} h, share_ratio: {:.2f}, last_activity: {}, tags: {}',
                entry['title'],
                entry['qbittorrent_completed'] / (1024 * 1024 * 1024),
                entry['qbittorrent_seeding_time'] / (60 * 60),
                entry['qbittorrent_share_ratio'],
                entry['qbittorrent_last_activity'],
                entry['qbittorrent_tags'])

    def remove_entries_cleaner(self, task: Task, cleaner_options: dict) -> None:
        delete_files = cleaner_options.get('delete_files')
        delete_hashes = []
        delete_files_hashes = []
        accepted_entry_hashes = []
        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        entry_dict = main_data_snapshot.get('entry_dict')
        reseed_dict = main_data_snapshot.get('reseed_dict')

        for entry in task.accepted:
            accepted_entry_hashes.append(entry['torrent_info_hash'])

        for entry_hash in accepted_entry_hashes:
            if entry_hash in delete_hashes or entry_hash in delete_files_hashes:
                continue
            server_entry = entry_dict.get(entry_hash)
            if not server_entry:
                self.client.reset_rid()
                continue
            save_path_with_name = server_entry.get('qbittorrent_save_path_with_name')
            reseed_entry_list = reseed_dict.get(save_path_with_name)
            torrent_hashes = []

            for reseed_entry in reseed_entry_list:
                torrent_hashes.append(reseed_entry['torrent_info_hash'])
            if not set(accepted_entry_hashes) >= set(torrent_hashes):
                delete_hashes.extend(set(accepted_entry_hashes) & set(torrent_hashes))
            else:
                delete_files_hashes.extend(torrent_hashes)
        if len(delete_hashes) > 0:
            self.client.delete_torrents('|'.join(delete_hashes), False)
            self.print_clean_log(entry_dict, delete_hashes, False)
        if len(delete_files_hashes) > 0:
            self.client.delete_torrents('|'.join(delete_files_hashes), delete_files)
            self.print_clean_log(entry_dict, delete_files_hashes, delete_files)

    def print_clean_log(self, entry_dict: dict, hashes: list[str], delete_files) -> None:
        for torrent_hash in hashes:
            entry = entry_dict.get(torrent_hash)
            logger.info(
                '{}, size: {:.2f} GiB, seeding_time: {:.2f} h, share_ratio: {:.2f}, last_activity: {}, tracker_msg: {}, tags: {}, delete_files: {}',
                entry['title'],
                entry['qbittorrent_completed'] / (1024 * 1024 * 1024),
                entry['qbittorrent_seeding_time'] / (60 * 60),
                entry['qbittorrent_share_ratio'],
                entry['qbittorrent_last_activity'],
                entry['qbittorrent_tracker_msg'],
                entry['qbittorrent_tags'],
                delete_files
            )

    def resume_entries(self, task: Task, resume_options: dict) -> None:
        recheck_torrents = resume_options.get('recheck_torrents')
        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        reseed_dict = main_data_snapshot.get('reseed_dict')
        hashes = []
        recheck_hashes = []
        if recheck_torrents:
            for entry in task.accepted:
                save_path_with_name = entry['qbittorrent_save_path_with_name']
                reseed_entry_list = reseed_dict.get(save_path_with_name)
                resume = False
                for reseed_entry in reseed_entry_list:
                    seeding = 'up' in reseed_entry['qbittorrent_state'].lower() and reseed_entry[
                        'qbittorrent_state'] != 'pausedUP'
                    if seeding:
                        hashes.append(entry['torrent_info_hash'])
                        logger.info('{}', entry['title'])
                        resume = True
                        break
                if not resume and entry['qbittorrent_state'] != 'checkingUP':
                    entry.reject(reason='can not find seeding torrent in same save path')
                    recheck_hashes.append(entry['torrent_info_hash'])
            if len(recheck_hashes) > 0:
                logger.info('recheck {}', recheck_hashes)
                self.client.recheck_torrents('|'.join(recheck_hashes))
        else:
            for entry in task.accepted:
                hashes.append(entry['torrent_info_hash'])
        self.client.resume_torrents('|'.join(hashes))

    def pause_entries(self, task: Task, pause_options: dict) -> None:
        if not pause_options:
            return
        hashes = []
        for entry in task.accepted:
            hashes.append(entry['torrent_info_hash'])
            logger.info('pause: {}', entry['title'])
        self.client.pause_torrents('|'.join(hashes))

    def modify_entries(self, task: Task, modify_options: dict) -> None:
        tag_by_tracker = modify_options.get('tag_by_tracker')
        modify_trackers = modify_options.get('modify_trackers')

        for entry in task.accepted:
            tags = entry.get('qbittorrent_tags')
            tags_modified = []
            torrent_trackers = entry.get('qbittorrent_trackers')
            for tracker in torrent_trackers:
                if tag_by_tracker:
                    site_name = net_utils.get_site_name(tracker.get('url'))
                    if site_name and site_name not in tags and site_name not in tags_modified:
                        tags_modified.append(site_name)
                if modify_trackers:
                    for regex, new_str in modify_trackers.items():
                        tracker_url = tracker.get('url')
                        if re.match(regex, tracker_url):
                            if new_str:
                                if re.match(regex, new_str):
                                    raise plugin.PluginError(
                                        f'{regex} matches {new_str}, this may cause a loop problem')
                                tracker_url_new = re.sub(regex, new_str, tracker_url)
                                self.client.edit_trackers(entry.get('torrent_info_hash'), tracker_url, tracker_url_new)
                                logger.info('{} update tracker {}', entry.get('title'), tracker_url_new)
                            else:
                                logger.info('{} remove tracker {}', entry.get('title'), tracker_url)
                                self.client.remove_trackers(entry.get('torrent_info_hash'), tracker_url)
            if tags_modified:
                self.client.add_torrent_tags(entry['torrent_info_hash'], ','.join(tags_modified))
                logger.info(f"{entry.get('title')} add tags {tags_modified}")

    def manage_conn_entries(self, task: Task, manage_conn_options: dict) -> None:
        min_conn = manage_conn_options.get('min')
        max_conn = manage_conn_options.get('max')
        for entry in task.accepted:
            step = entry.get('step')
            if not step:
                return
            server_state = entry.get('server_state')
            server_queued_io_jobs = server_state.get('queued_io_jobs')
            server_total_peer_connections = server_state.get('total_peer_connections')
            application_preferences = self.client.get_application_preferences()
            max_connect = application_preferences.get('max_connec')
            if max_connect == -1:
                max_connect = float('inf')
            if (step > 0 and max_connect <= server_total_peer_connections) or step < 0:
                max_connect_changed = server_total_peer_connections + step
                if max_connect_changed < min_conn:
                    max_connect_changed = min_conn
                elif max_connect_changed > max_conn:
                    max_connect_changed = max_conn

                self.client.set_application_preferences('{{"max_connec": {}}}'.format(max_connect_changed))
                logger.debug('queued_io_jobs: {} , total_peer_connections: {}, set max_connec to {}',
                             server_queued_io_jobs, server_total_peer_connections, max_connect_changed)

    def limit_upload_by_tracker_entries(self, task: Task, limit_when_not_working_options: dict) -> None:
        working_speed = limit_when_not_working_options.get('working')
        not_working_speed = limit_when_not_working_options.get('not_working')
        working_hashes = []
        not_working_hashes = []
        for entry in task.accepted:
            torrent_trackers = entry.get('qbittorrent_trackers')
            is_working = False
            updating = False
            for tracker in torrent_trackers:
                status = tracker.get('status')
                if status == 2:
                    is_working = True
                elif status == 3:
                    updating = True
            if updating:
                continue
            up_limit = 0 if entry['qbittorrent_up_limit'] == -1 else entry['qbittorrent_up_limit']
            if is_working:
                entry_working = entry.get('working') if entry.get('working') else working_speed
                if up_limit != entry_working:
                    if entry.get('working'):
                        self.client.set_torrent_upload_limit(entry['torrent_info_hash'], entry_working)
                    else:
                        working_hashes.append(entry['torrent_info_hash'])
                    logger.debug(
                        f'{entry["title"]} tags: {entry["qbittorrent_tags"]} tracker is working, set torrent upload limit to {entry_working} B/s')
            elif up_limit != not_working_speed:
                not_working_hashes.append(entry['torrent_info_hash'])
                logger.debug(
                    f'{entry["title"]} tags: {entry["qbittorrent_tags"]} tracker is not working, set torrent upload limit to {not_working_speed} B/s')
        if working_hashes:
            self.client.set_torrent_upload_limit('|'.join(working_hashes), working_speed)
        if not_working_hashes:
            self.client.set_torrent_upload_limit('|'.join(not_working_hashes), not_working_speed)

    def refresh_tracker_entries(self, task: Task, refresh_tracker_options: dict) -> None:
        prefix = 'refresh:'
        for entry in task.accepted:
            torrent_trackers = entry.get('qbittorrent_trackers')
            for tracker in torrent_trackers:
                tracker_url = tracker.get('url')

                if tracker_url.startswith(prefix):
                    self.client.edit_trackers(entry.get('torrent_info_hash'), tracker_url, tracker_url[len(prefix):])
                else:
                    self.client.edit_trackers(entry.get('torrent_info_hash'), tracker_url, prefix + tracker_url)
                    self.client.edit_trackers(entry.get('torrent_info_hash'), prefix + tracker_url, tracker_url)


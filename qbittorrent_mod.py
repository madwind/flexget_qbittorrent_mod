import math
import os
import re
from datetime import datetime

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from loguru import logger

from .ptsites.client.qbittorrent_client import QBittorrentClientFactory


class QBittorrentModBase:
    def __init__(self):
        self.client = None

    def prepare_config(self, config):
        if isinstance(config, bool):
            config = {'enabled': config}
        config.setdefault('enabled', True)
        config.setdefault('host', 'localhost')
        config.setdefault('port', 8080)
        config.setdefault('use_ssl', False)
        config.setdefault('verify_cert', True)
        return config

    def create_client(self, config):
        client = QBittorrentClientFactory().get_client(config)
        return client

    def on_task_start(self, task, config):
        self.client = None
        config = self.prepare_config(config)
        if config['enabled']:
            if task.options.test:
                logger.info('Trying to connect to qBittorrent...')
                self.client = self.create_client(config)
                if self.client:
                    logger.info('Successfully connected to qBittorrent.')
                else:
                    logger.error('It looks like there was a problem connecting to qBittorrent.')


class PluginQBittorrentModInput(QBittorrentModBase):
    schema = {
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'use_ssl': {'type': 'boolean'},
            'port': {'type': 'integer'},
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'verify_cert': {'type': 'boolean'},
            'server_state': {'type': 'boolean'},
            'enabled': {'type': 'boolean'},
        },
        'additionalProperties': False
    }

    def prepare_config(self, config):
        config = QBittorrentModBase.prepare_config(self, config)
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        if not config['enabled']:
            return
        if config.get('server_state'):
            entry = Entry(
                title='qBittorrent',
                url=''
            )
            entry['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry['server_state'] = {}
            try:
                self.client = self.create_client(config)
                entry['server_state'] = self.client.get_main_data_snapshot(id(task)).get('server_state')
                entry['server_state']['flexget_connected'] = True
            except plugin.PluginError:
                entry['server_state']['flexget_connected'] = False
            return [entry]
        else:
            self.client = self.create_client(config)
            return list(self.client.get_main_data_snapshot(id(task)).get('entry_dict').values())


class PluginQBittorrentMod(QBittorrentModBase):
    schema = {
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'use_ssl': {'type': 'boolean'},
            'port': {'type': 'integer'},
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'verify_cert': {'type': 'boolean'},
            'action': {
                'type': 'object',
                'properties': {
                    'add': {
                        'type': 'object',
                        'properties': {
                            'savepath': {'type': 'string'},
                            'cookie': {'type': 'string'},
                            'category': {'type': 'string'},
                            'skip_checking': {'type': 'boolean'},
                            'paused': {'type': 'string'},
                            'root_folder': {'type': 'string'},
                            'rename': {'type': 'string'},
                            'upLimit': {'type': 'integer'},
                            'dlLimit': {'type': 'integer'},
                            'autoTMM': {'type': 'boolean'},
                            'sequentialDownload': {'type': 'string'},
                            'firstLastPiecePrio': {'type': 'string'},
                            'reject_on_dl_speed': {'oneOf': [{'type': 'boolean'}, {'type': 'integer'}]},
                            'reject_on_dl_limit': {'oneOf': [{'type': 'boolean'}, {'type': 'integer'}]},
                        }
                    },
                    'remove': {
                        'type': 'object',
                        'properties': {
                            'check_reseed': {
                                'oneOf': [{'type': 'boolean'}, {'type': 'array', 'items': {'type': 'string'}}]},
                            'delete_files': {'type': 'boolean'},
                            'keep_disk_space': {'type': 'integer'},
                            'dl_limit_on_succeeded': {'type': 'integer'},
                            'alt_dl_limit_on_succeeded': {'type': 'integer'},
                            'dl_limit_interval': {'type': 'integer'},
                            'show_entry': {'type': 'string'}
                        }
                    },
                    'resume': {
                        'type': 'object',
                        'properties': {
                            'recheck_torrents': {'type': 'boolean'},
                        }
                    },
                    'pause': {
                        'type': 'boolean'
                    },
                    'modify': {
                        'type': 'object',
                        'properties': {
                            'tag_by_tracker': {'type': 'boolean'},
                            'replace_trackers': {
                                'type': 'object',
                                'properties': {
                                }
                            }
                        }
                    }
                }
            },
            'fail_html': {'type': 'boolean'}
        },
        'additionalProperties': False,
    }

    def prepare_config(self, config):
        config = super().prepare_config(config)
        config.setdefault('fail_html', True)
        config.setdefault('action', {})
        return config

    @plugin.priority(120)
    def on_task_download(self, task, config):
        config = self.prepare_config(config)
        add_options = config.get('action').get('add')
        if not add_options:
            return

        if not self.client:
            self.client = self.create_client(config)
            if self.client:
                logger.debug('Successfully connected to qBittorrent.')
            else:
                raise plugin.PluginError("Couldn't connect to qBittorrent.")

        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        server_state = main_data_snapshot.get('server_state')

        reject_on_dl_limit = add_options.get('reject_on_dl_limit')
        reject_reason = ''

        if reject_on_dl_limit:
            dl_rate_limit = server_state.get('dl_rate_limit')
            if dl_rate_limit and dl_rate_limit < reject_on_dl_limit:
                reject_reason = 'dl_limit < reject_on_dl_limit'

        reject_on_dl_speed = add_options.get('reject_on_dl_speed')
        if reject_on_dl_speed:
            dl_info_speed = server_state.get('dl_info_speed')
            if dl_info_speed and dl_info_speed > reject_on_dl_speed:
                reject_reason = 'dl_speed > reject_on_dl_speed'

        if reject_on_dl_limit is not None:
            del add_options['reject_on_dl_limit']
        if reject_on_dl_speed is not None:
            del add_options['reject_on_dl_speed']

        for entry in task.accepted:
            if reject_reason:
                entry.reject(reason=reject_reason, remember=True)
                site_name = self._get_site_name(entry.get('url'))
                logger.info('reject {}, because: {}, site: {}', entry['title'], reject_reason, site_name)
                continue

        if 'download' not in task.config:
            download = plugin.get('download', self)
            download.get_temp_files(task, handle_magnets=True, fail_html=config['fail_html'])

    @plugin.priority(135)
    def on_task_output(self, task, config):
        config = self.prepare_config(config)
        action_config = config.get('action')
        if len(action_config) != 1:
            raise plugin.PluginError('There must be and only one action')
        # don't add when learning
        if task.options.learn:
            return
        if not task.accepted and not action_config.get('remove'):
            return
        if not self.client:
            self.client = self.create_client(config)
            if self.client:
                logger.debug('Successfully connected to qBittorrent.')
            else:
                raise plugin.PluginError("Couldn't connect to qBittorrent.")

        (action_name, option), = action_config.items()
        action = getattr(self, action_name + '_entries', None)
        if action:
            action(task, option)
        else:
            raise plugin.PluginError('Unknown action.')

    def add_entries(self, task, add_options):
        for entry in task.accepted:
            add_options['autoTMM'] = entry.get('autoTMM', add_options.get('autoTMM'))
            add_options['category'] = entry.get('category', add_options.get('category'))
            add_options['savepath'] = entry.get('savepath', add_options.get('savepath'))
            add_options['paused'] = entry.get('paused', add_options.get('paused'))

            if add_options.get('autoTMM') and not add_options.get('category'):
                del add_options['savepath']

            if not add_options.get('paused'):
                del add_options['paused']

            is_magnet = entry['url'].startswith('magnet:')

            if task.manager.options.test:
                logger.info('Test mode.')
                logger.info('Would add torrent to qBittorrent with:')
                if not is_magnet:
                    logger.info('File: {}', entry.get('file'))
                else:
                    logger.info('Url: {}', entry.get('url'))
                logger.info('Save path: {}', add_options.get('savepath'))
                logger.info('Category: {}', add_options.get('category'))
                logger.info('Paused: {}', add_options.get('paused', 'false'))
                if add_options.get('upLimit'):
                    logger.info('Upload Speed Limit: {}', add_options.get('upLimit'))
                if add_options.get('dlLimit'):
                    logger.info('Download Speed Limit: {}', add_options.get('dlLimit'))
                return

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
                self.client.add_torrent_file(entry['file'], add_options)
            else:
                self.client.add_torrent_url(entry['url'], add_options)

    def remove_entries(self, task, remove_options):
        delete_files = remove_options.get('delete_files')
        check_reseed = remove_options.get('check_reseed')
        keep_disk_space = remove_options.get('keep_disk_space')

        dl_limit_interval = remove_options.get('dl_limit_interval', 24 * 60 * 60)
        show_entry = remove_options.get('show_entry')
        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        server_state = main_data_snapshot.get('server_state')

        dl_rate_limit = server_state.get('dl_rate_limit')
        use_alt_speed_limits = server_state.get('use_alt_speed_limits')
        free_space_on_disk = server_state.get('free_space_on_disk')

        dl_limit_mode = 'dl_limit'
        dl_limit_on_succeeded = remove_options.get('dl_limit_on_succeeded', 0)
        alt_dl_limit_on_succeeded = remove_options.get('alt_dl_limit_on_succeeded', 0)
        if use_alt_speed_limits:
            dl_limit_mode = 'alt_dl_limit'
            dl_limit_on_succeeded = alt_dl_limit_on_succeeded

        if keep_disk_space:
            keep_disk_space = keep_disk_space * 1024 * 1024 * 1024
            if keep_disk_space < free_space_on_disk:
                if dl_limit_on_succeeded is not None:
                    dl_limit = math.floor(dl_limit_on_succeeded / 1024) * 1024
                    if dl_limit != dl_rate_limit:
                        self.client.set_application_preferences('{{"{}": {}}}'.format(dl_limit_mode, dl_limit))
                        logger.info("set {} to {} KiB/s", dl_limit_mode, dl_limit / 1024)
                return
            else:
                if not task.accepted:
                    dl_limit = free_space_on_disk / dl_limit_interval
                    if dl_limit_on_succeeded and dl_limit > dl_limit_on_succeeded:
                        dl_limit = dl_limit_on_succeeded
                    dl_limit = math.floor(dl_limit / 1024) * 1024
                    if dl_limit != dl_rate_limit:
                        self.client.set_application_preferences('{{"{}": {}}}'.format(dl_limit_mode, dl_limit))
                        logger.warning(
                            "not enough disk space, but There are no eligible torrents, set {} to {} KiB/s",
                            dl_limit_mode,
                            dl_limit / 1024)
                    return

        if not task.accepted:
            return

        entry_dict = main_data_snapshot.get('entry_dict')
        reseed_dict = main_data_snapshot.get('reseed_dict')
        accepted_entry_hashes = []
        delete_hashes = []

        delete_size = 0
        entry_index = 0
        entry_show_index = -1
        for entry in task.accepted:
            entry_index = entry_index + 1
            if show_entry and entry['torrent_info_hash'] == show_entry:
                entry_show_index = entry_index
            accepted_entry_hashes.append(entry['torrent_info_hash'])

        if show_entry:
            entry_found = entry_dict.get(show_entry)
            if entry_found:
                logger.info('hash: {} ,index : {}', entry_found['torrent_info_hash'], entry_show_index)
                for key, value in entry_found.items():
                    logger.info('key: {}, value: {}', key, value)

        for entry_hash in accepted_entry_hashes:
            if entry_hash in delete_hashes:
                continue
            save_path_with_name = entry_dict.get(entry_hash).get('qbittorrent_save_path_with_name')
            reseed_entry_list = reseed_dict.get(save_path_with_name)
            check_hashes = []
            torrent_hashes = []
            torrent_size = 0

            for reseed_entry in reseed_entry_list:
                if reseed_entry['qbittorrent_completed'] != 0:
                    torrent_size = reseed_entry['qbittorrent_completed']
                if isinstance(check_reseed, list):
                    trackers = reseed_entry['qbittorrent_trackers']
                    site_names = []
                    for tracker in trackers:
                        site_names.append(self._get_site_name(tracker.get('url')))

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
            else:
                if keep_disk_space:
                    if keep_disk_space > free_space_on_disk + delete_size:
                        delete_size += torrent_size
                        self._build_delete_hashes(delete_hashes, torrent_hashes, entry_dict, keep_disk_space,
                                                  free_space_on_disk, delete_size)
                        if keep_disk_space < free_space_on_disk + delete_size:
                            break
                else:
                    self._build_delete_hashes(delete_hashes, torrent_hashes, entry_dict, keep_disk_space,
                                              free_space_on_disk, delete_size)
        if dl_limit_on_succeeded is not None:
            if keep_disk_space > free_space_on_disk + delete_size:
                dl_limit = (free_space_on_disk + delete_size) / dl_limit_interval
                if dl_limit_on_succeeded and dl_limit > dl_limit_on_succeeded:
                    dl_limit = dl_limit_on_succeeded
                dl_limit = math.floor(dl_limit / 1024) * 1024
                if dl_limit != dl_rate_limit:
                    self.client.set_application_preferences('{{"{}": {}}}'.format(dl_limit_mode, dl_limit))
                    logger.warning("not enough disk space, set {} to {} KiB/s", dl_limit_mode, dl_limit / 1024)
        if len(delete_hashes) > 0:
            self.client.delete_torrents(str.join('|', delete_hashes), delete_files)

    def _build_delete_hashes(self, delete_hashes, torrent_hashes, all_entry_map, keep_disk_space, free_space_on_disk,
                             delete_size):
        delete_hashes.extend(torrent_hashes)
        logger.info('keep_disk_space: {:.2F} GB, free_space_on_disk: {:.2f} GB, delete_size: {:.2f} GB',
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
                '{}, size: {:.2f} GB, seeding_time: {:.2f} h, share_ratio: {:.2f}, last_activity: {},  site: {}',
                entry['title'],
                entry['qbittorrent_completed'] / (1024 * 1024 * 1024),
                entry['qbittorrent_seeding_time'] / (60 * 60),
                entry['qbittorrent_share_ratio'],
                entry['qbittorrent_last_activity'],
                entry['qbittorrent_tags'])

    def resume_entries(self, task, resume_options):
        recheck_torrents = resume_options.get('recheck_torrents')
        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        reseed_dict = main_data_snapshot.get('reseed_dict')
        hashes = []
        recheck_hashes = []
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
        if recheck_torrents and len(recheck_hashes) > 0:
            logger.info('recheck {}', recheck_hashes)
            self.client.recheck_torrents(str.join('|', recheck_hashes))
        self.client.resume_torrents(str.join('|', hashes))

    def pause_entries(self, task, pause_options):
        if not pause_options:
            return
        hashes = []
        for entry in task.accepted:
            hashes.append(entry['torrent_info_hash'])
            logger.info('pause: {}', entry['title'])
        self.client.pause_torrents(str.join('|', hashes))

    def modify_entries(self, task, modify_options):
        tag_by_tracker = modify_options.get('tag_by_tracker')
        replace_trackers = modify_options.get('replace_trackers')
        for entry in task.accepted:
            tags = entry.get('qbittorrent_tags')
            torrent_trackers = entry.get('qbittorrent_trackers')
            add_tag = False
            modify_tracker = False
            for tracker in torrent_trackers:
                if tag_by_tracker:
                    site_name = self._get_site_name(tracker.get('url'))
                    if not add_tag and site_name and site_name not in tags:
                        self.client.add_torrent_tags(entry['torrent_info_hash'], site_name)
                        add_tag = True
                        logger.info('{} add tag {}', entry.get('title'), site_name)
                if replace_trackers:
                    for orig_url, new_url in replace_trackers.items():
                        if tracker.get('url') == orig_url:
                            self.client.edit_trackers(entry.get('torrent_info_hash'), orig_url, new_url)
                            modify_tracker = True
                            logger.info('{} update tracker {}', entry.get('title'), new_url)
            if not add_tag and not modify_tracker:
                entry.reject()

    def _get_site_name(self, tracker_url):
        re_object = re.search('(?<=//).*?(?=/)', tracker_url)
        if re_object:
            domain = re_object.group().split('.')
            if len(domain) > 1:
                site_name = domain[len(domain) - 2]
                if site_name == 'edu':
                    site_name = domain[len(domain) - 3]
                return site_name

    def on_task_learn(self, task, config):
        """ Make sure all temp files are cleaned up when entries are learned """
        # If download plugin is enabled, it will handle cleanup.
        if 'download' not in task.config:
            download = plugin.get('download', self)
            download.cleanup_temp_files(task)

    on_task_abort = on_task_learn


@event('plugin.register')
def register_plugin():
    plugin.register(PluginQBittorrentMod, 'qbittorrent_mod', api_ver=2)
    plugin.register(PluginQBittorrentModInput, 'from_qbittorrent_mod', api_ver=2)

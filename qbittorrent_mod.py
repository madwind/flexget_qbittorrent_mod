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
            'server_state': {'oneOf': [{'type': 'boolean'}, {'type': 'string'}]},
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
        server_state = config.get('server_state')
        if server_state:
            entry = Entry(
                title='qBittorrent Server State' if isinstance(server_state, bool) else server_state,
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
                            'reject_on': {
                                'type': 'object',
                                'properties': {
                                    'bandwidth_limit': {'type': 'integer'},
                                    'dl_speed': {
                                        'oneOf': [
                                            {'type': 'boolean'},
                                            {'type': 'integer'},
                                            {'type': 'number', 'minimum': 0.1, 'maximum': 0.9},
                                        ]
                                    },
                                    'dl_limit': {'oneOf': [{'type': 'boolean'}, {'type': 'integer'}]}
                                }
                            }
                        }
                    },
                    'remove': {
                        'type': 'object',
                        'properties': {
                            'keeper': {
                                'type': 'object',
                                'properties': {
                                    'keep_disk_space': {'type': 'integer'},
                                    'check_reseed': {
                                        'oneOf': [{'type': 'boolean'}, {'type': 'array', 'items': {'type': 'string'}}]},
                                    'delete_files': {'type': 'boolean'},
                                    'dl_limit_on_succeeded': {'type': 'integer'},
                                    'alt_dl_limit_on_succeeded': {'type': 'integer'},
                                    'dl_limit_interval': {'type': 'integer'}
                                },
                            },
                            'cleaner': {
                                'type': 'object',
                                'properties': {
                                    'delete_files': {'type': 'boolean'}
                                }
                            }
                        },
                        "minProperties": 1,
                        "maxProperties": 1,
                    },
                    'resume': {
                        'type': 'object',
                        'properties': {
                            'recheck_torrents': {'type': 'boolean'}
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
                    },
                    'manage_conn': {
                        'type': 'object',
                        'properties': {
                            'min': {'type': 'integer'},
                            'max': {'type': 'integer'}
                        }
                    }
                },
                "minProperties": 1,
                "maxProperties": 1,
            },
            'fail_html': {'type': 'boolean'},
        },
        'additionalProperties': False
    }

    def prepare_config(self, config):
        config = super().prepare_config(config)
        config.setdefault('fail_html', True)
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

        reject_on = add_options.get('reject_on')
        max_dl_speed = reject_on.get('max_dl_speed')
        reject_on_dl_speed = reject_on.get('dl_speed')
        reject_on_dl_limit = reject_on.get('dl_limit')
        reject_reason = ''

        dl_rate_limit = server_state.get('dl_rate_limit')

        if reject_on_dl_limit:
            if dl_rate_limit and dl_rate_limit < reject_on_dl_limit:
                reject_reason = 'dl_limit: {:.2F} MiB < reject_on_dl_limit: {:.2F} MiB'.format(
                    dl_rate_limit / (1024 * 1024), reject_on_dl_limit / (1024 * 1024))

        if reject_on_dl_speed:
            if isinstance(reject_on_dl_speed, float):
                dl_rate_limit = dl_rate_limit if dl_rate_limit else max_dl_speed
                reject_on_dl_speed = int(dl_rate_limit * reject_on_dl_speed)
            dl_info_speed = server_state.get('dl_info_speed')
            if dl_info_speed and dl_info_speed > reject_on_dl_speed:
                reject_reason = 'dl_speed: {:.2F} MiB > reject_on_dl_speed: {:.2F} MiB'.format(
                    dl_info_speed / (1024 * 1024), reject_on_dl_speed / (1024 * 1024))

        if reject_on is not None:
            del add_options['reject_on']

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
        (mode_name, option), = remove_options.items()
        mode = getattr(self, 'remove_entries_' + mode_name, None)
        if mode:
            mode(task, option)
        else:
            raise plugin.PluginError('Unknown mode.')

    def remove_entries_keeper(self, task, keeper_options):
        delete_files = keeper_options.get('delete_files')
        check_reseed = keeper_options.get('check_reseed')
        keep_disk_space = keeper_options.get('keep_disk_space')

        dl_limit_interval = keeper_options.get('dl_limit_interval', 24 * 60 * 60)
        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        server_state = main_data_snapshot.get('server_state')

        dl_rate_limit = server_state.get('dl_rate_limit')
        use_alt_speed_limits = server_state.get('use_alt_speed_limits')
        free_space_on_disk = server_state.get('free_space_on_disk')

        dl_limit_mode = 'dl_limit'
        dl_limit_on_succeeded = keeper_options.get('dl_limit_on_succeeded', 0)
        alt_dl_limit_on_succeeded = keeper_options.get('alt_dl_limit_on_succeeded', 0)
        if use_alt_speed_limits:
            dl_limit_mode = 'alt_dl_limit'
            dl_limit_on_succeeded = alt_dl_limit_on_succeeded

        keep_disk_space = keep_disk_space * 1024 * 1024 * 1024
        if keep_disk_space < free_space_on_disk:
            if dl_limit_on_succeeded is not None:
                dl_limit = math.floor(dl_limit_on_succeeded / 1024) * 1024
                if dl_limit != dl_rate_limit:
                    self.client.set_application_preferences('{{"{}": {}}}'.format(dl_limit_mode, dl_limit))
                    logger.info("set {} to {} KiB/s", dl_limit_mode, dl_limit / 1024)
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
                if keep_disk_space > free_space_on_disk + delete_size:
                    delete_size += torrent_size
                    self._build_delete_hashes(delete_hashes, torrent_hashes, entry_dict, keep_disk_space,
                                              free_space_on_disk, delete_size)
                    if keep_disk_space < free_space_on_disk + delete_size:
                        break
        self.calc_and_set_dl_limit(keep_disk_space, free_space_on_disk, delete_size, dl_limit_interval,
                                   dl_limit_on_succeeded, dl_rate_limit, dl_limit_mode)
        if len(delete_hashes) > 0:
            self.client.delete_torrents(str.join('|', delete_hashes), delete_files)

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
                '{}, size: {:.2f} GB, seeding_time: {:.2f} h, share_ratio: {:.2f}, last_activity: {}, site: {}',
                entry['title'],
                entry['qbittorrent_completed'] / (1024 * 1024 * 1024),
                entry['qbittorrent_seeding_time'] / (60 * 60),
                entry['qbittorrent_share_ratio'],
                entry['qbittorrent_last_activity'],
                entry['qbittorrent_tags'])

    def remove_entries_cleaner(self, task, cleaner_options):
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
            save_path_with_name = entry_dict.get(entry_hash).get('qbittorrent_save_path_with_name')
            reseed_entry_list = reseed_dict.get(save_path_with_name)
            torrent_hashes = []

            for reseed_entry in reseed_entry_list:
                torrent_hashes.append(reseed_entry['torrent_info_hash'])
            if not set(accepted_entry_hashes) >= set(torrent_hashes):
                delete_hashes.extend(set(accepted_entry_hashes) & set(torrent_hashes))
            else:
                delete_files_hashes.extend(torrent_hashes)
        if len(delete_hashes) > 0:
            self.client.delete_torrents(str.join('|', delete_hashes), False)
            self.print_clean_log(entry_dict, delete_hashes, False)
        if len(delete_files_hashes) > 0:
            self.client.delete_torrents(str.join('|', delete_files_hashes), delete_files)
            self.print_clean_log(entry_dict, delete_files_hashes, delete_files)

    def print_clean_log(self, entry_dict, hashes, delete_files):
        for torrent_hash in hashes:
            entry = entry_dict.get(torrent_hash)
            logger.info(
                '{}, size: {:.2f} GiB, seeding_time: {:.2f} h, share_ratio: {:.2f}, last_activity: {}, tracker_msg: {}, site: {}, delete_files: {}',
                entry['title'],
                entry['qbittorrent_completed'] / (1024 * 1024 * 1024),
                entry['qbittorrent_seeding_time'] / (60 * 60),
                entry['qbittorrent_share_ratio'],
                entry['qbittorrent_last_activity'],
                entry['qbittorrent_tracker_msg'],
                entry['qbittorrent_tags'],
                delete_files
            )

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
            for tracker in torrent_trackers:
                if tag_by_tracker:
                    site_name = self._get_site_name(tracker.get('url'))
                    if not add_tag and site_name and site_name not in tags:
                        self.client.add_torrent_tags(entry['torrent_info_hash'], site_name)
                        logger.info('{} add tag {}', entry.get('title'), site_name)
                if replace_trackers:
                    for orig_url, new_url in replace_trackers.items():
                        if tracker.get('url') == orig_url:
                            if new_url:
                                self.client.edit_trackers(entry.get('torrent_info_hash'), orig_url, new_url)
                                logger.info('{} update tracker {}', entry.get('title'), new_url)
                            else:
                                self.client.remove_trackers(entry.get('torrent_info_hash'), orig_url)
                                logger.info('{} remove tracker {}', entry.get('title'), orig_url)

    def manage_conn_entries(self, task, manage_conn_options):
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
            if (step > 0 and max_connect <= server_total_peer_connections) or (
                    step < 0 and max_connect >= server_total_peer_connections):
                max_connect_changed = server_total_peer_connections + step
                if max_connect_changed < min_conn:
                    max_connect_changed = min_conn
                elif max_connect_changed > max_conn:
                    max_connect_changed = max_conn

                self.client.set_application_preferences('{{"max_connec": {}}}'.format(max_connect_changed))
                logger.info('queued_io_jobs: {} , total_peer_connections: {}, set max_connec to {}',
                            server_queued_io_jobs, server_total_peer_connections, max_connect_changed)

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

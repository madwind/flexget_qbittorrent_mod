import math
import os
import re
import sys
from os import path

from flexget import plugin
from flexget.event import event
from loguru import logger

d = path.dirname(__file__)
sys.path.append(d)

from qbittorrent_client import QBittorrentClientFactory


class QBittorrentModBase:
    def __init__(self):
        self.client = None

    def prepare_config(self, config):
        if isinstance(config, bool):
            config = {'enabled': config}
        config.setdefault('enabled', True)
        config.setdefault('host', 'localhost')
        config.setdefault('port', 8080)
        config.setdefault('use_ssl', True)
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
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'host': {'type': 'string'},
                    'use_ssl': {'type': 'boolean'},
                    'port': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'password': {'type': 'string'},
                    'verify_cert': {'type': 'boolean'},
                    'enabled': {'type': 'boolean'},
                },
                'additionalProperties': False
            }
        ]
    }

    def prepare_config(self, config):
        config = QBittorrentModBase.prepare_config(self, config)
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)

        if not config['enabled']:
            return
        if not self.client:
            self.client = self.create_client(config)
        return list(self.client.get_task_data(id(task)).get('entry_dict').values())


class PluginQBittorrentMod(QBittorrentModBase):
    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
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
                                    'firstLastPiecePrio': {'type': 'string'}
                                }
                            },
                            'remove': {
                                'type': 'object',
                                'properties': {
                                    'check_reseed': {'type': 'boolean'},
                                    'delete_files': {'type': 'boolean'},
                                    'keep_disk_space': {'type': 'integer'},
                                    'dl_limit_on_succeeded': {'type': 'integer'}
                                }
                            },
                            'resume': {
                                'type': 'object',
                                'properties': {
                                    'recheck_torrents': {'type': 'boolean'},
                                }
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
        ]
    }

    def prepare_config(self, config):
        config = super().prepare_config(config)
        config.setdefault('fail_html', True)
        config.setdefault('action', {})
        return config

    @plugin.priority(120)
    def on_task_download(self, task, config):
        """
        Call download plugin to generate torrent files to load into
        qBittorrent.
        """
        config = self.prepare_config(config)
        if not config['enabled']:
            return
        # If the download plugin is not enabled, we need to call it to get our temp .torrent files

        if 'download' not in task.config:
            download = plugin.get('download', self)
            for entry in task.accepted:
                if entry.get('transmission_id'):
                    # The torrent is already loaded in deluge, we don't need to get anything
                    continue
                if list(config['action'])[0] != 'add' and entry.get('torrent_info_hash'):
                    # If we aren't adding the torrent new, all we need is info hash
                    continue
                download.get_temp_file(task, entry, handle_magnets=True, fail_html=config['fail_html'])

    @plugin.priority(135)
    def on_task_output(self, task, config):
        config = self.prepare_config(config)
        action_config = config.get('action')
        if len(action_config) != 1:
            raise plugin.PluginError('There must be and only one action')
        # don't add when learning
        if task.options.learn:
            return
        if not config['enabled']:
            return
            # Do not run if there is nothing to do
        if not task.accepted or not action_config.get('remove'):
            return
        if not self.client:
            self.client = self.create_client(config)
            if self.client:
                logger.debug('Successfully connected to qBittorrent.')
            else:
                raise plugin.PluginError("Couldn't connect to qBittorrent.")

        if action_config.get('add'):
            for entry in task.accepted:
                self.add_entries(task, entry, action_config)
        elif action_config.get('remove'):
            self.remove_entries(task, action_config)
        elif action_config.get('resume'):
            self.resume_entries(task, action_config)
        elif action_config.get('modify'):
            self.modify_entries(task, action_config)
        else:
            raise plugin.PluginError('Unknown action.')

    def on_task_exit(self, task, config):
        config = self.prepare_config(config)
        if not self.client:
            self.client = self.create_client(config)
            if self.client:
                logger.debug('Successfully connected to qBittorrent.')
            else:
                raise plugin.PluginError("Couldn't connect to qBittorrent.")
        self.client.del_task_data(id(task))

    def add_entries(self, task, entry, config):
        add_options = config.get('add')

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

    def remove_entries(self, task, config):
        remove_options = config.get('remove')
        delete_files = remove_options.get('delete_files')
        check_reseed = remove_options.get('check_reseed')
        keep_disk_space = remove_options.get('keep_disk_space')
        dl_limit_on_succeeded = remove_options.get('dl_limit_on_succeeded')
        task_data = self.client.get_task_data(id(task))
        server_state = task_data.get('server_state')
        free_space_on_disk = 0

        if keep_disk_space:
            keep_disk_space = keep_disk_space * 1024 * 1024 * 1024
            free_space_on_disk = server_state.get('free_space_on_disk')
            if keep_disk_space < free_space_on_disk:
                if dl_limit_on_succeeded is not None:
                    self.client.set_application_preferences('{{"dl_limit": {}}}'.format(dl_limit_on_succeeded))
                    logger.debug("set dl_limit to {} KiB/s", dl_limit_on_succeeded / 1024)
                return
            else:
                if not task.accepted:
                    dl_limit = math.ceil(free_space_on_disk / (24 * 60 * 60))
                    self.client.set_application_preferences('{{"dl_limit": {}}}'.format(dl_limit))
                    logger.warning(
                        "not enough disk space, but There are no eligible torrents, set dl_limit to {} KiB/s",
                        math.ceil(dl_limit / 1024))
                    return

        if not task.accepted:
            return

        entry_dict = task_data.get('entry_dict')
        reseed_dict = task_data.get('reseed_dict')
        accepted_entry_hashes = []
        delete_hashes = []

        delete_size = 0
        for entry in task.accepted:
            accepted_entry_hashes.append(entry['torrent_info_hash'])

        for entry_hash in accepted_entry_hashes:
            if entry_hash in delete_hashes:
                continue
            save_path_with_name = entry_dict.get(entry_hash).get('qbittorrent_save_path_with_name')
            reseed_entry_list = reseed_dict.get(save_path_with_name)
            torrent_hashes = []
            torrent_size = 0

            for reseed_entry in reseed_entry_list:
                if reseed_entry['qbittorrent_completed'] != 0:
                    torrent_size = reseed_entry['qbittorrent_completed']
                torrent_hashes.append(reseed_entry['torrent_info_hash'])
            if check_reseed and not set(accepted_entry_hashes) >= set(torrent_hashes):
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
                dl_limit = math.ceil((free_space_on_disk - delete_size) / (24 * 60 * 60))
                self.client.set_application_preferences('{{"dl_limit": {}}}'.format(dl_limit))
                logger.warning("not enough disk space, set dl_limit to {} KiB/s", math.ceil(dl_limit / 1024))

        self.client.delete_torrents(str.join('|', delete_hashes), delete_files)

    def _build_delete_hashes(self, delete_hashes, torrent_hashes, all_entry_map, keep_disk_space, free_space_on_disk,
                             delete_size):
        delete_hashes.extend(torrent_hashes)
        logger.info('keep_disk_space: {:.2F} GB, free_space_on_disk: {:.2f} GB, delete_size: {:.2f} GB',
                    keep_disk_space / (1024 * 1024 * 1024), free_space_on_disk / (1024 * 1024 * 1024),
                    delete_size / (1024 * 1024 * 1024))
        for torrent_hash in torrent_hashes:
            entry = all_entry_map.get(torrent_hash)
            entry.accept(reason='torrent with the same save path are all pass tested')
            logger.info('{}, site: {}, size: {:.2f} GB, last_activity: {}', entry.get('title'),
                        entry.get('qbittorrent_tags'),
                        entry.get('qbittorrent_completed') / (1024 * 1024 * 1024),
                        entry.get('qbittorrent_last_activity'))

    def resume_entries(self, task, config):
        resume_options = config.get('resume')
        recheck_torrents = resume_options.get('recheck_torrents')
        task_data = self.client.get_task_data(id(task))
        reseed_dict = task_data.get('reseed_dict')
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
            if not resume:
                entry.reject('can not find seeding torrent in same save path')
                recheck_hashes.append(entry['torrent_info_hash'])
        if recheck_torrents and len(recheck_hashes) > 0:
            logger.info('recheck {}', recheck_hashes)
            self.client.recheck_torrents(str.join('|', recheck_hashes))
        self.client.resume_torrents(str.join('|', hashes))

    def modify_entries(self, task, config):
        modify_options = config.get('modify')
        tag_by_tracker = modify_options.get('tag_by_tracker')
        replace_tracker = modify_options.get('replace_tracker')
        for entry in task.accepted:
            tags = entry.get('qbittorrent_tags')
            torrent_trackers = entry.get('qbittorrent_trackers')
            for tracker in torrent_trackers:
                modify = False
                if tag_by_tracker:
                    site_name = self._get_site_name(tracker.get('url'))
                    if site_name and site_name not in tags:
                        self.client.add_torrent_tags(entry['torrent_info_hash'], site_name)
                        modify = True
                        logger.info('{} add tag {}', entry.get('title'), site_name)
                if replace_tracker:
                    for orig_url, new_url in replace_tracker.items():
                        if tracker.get('url') == orig_url:
                            self.client.edit_trackers(entry.get('torrent_info_hash'), orig_url, new_url)
                            modify = True
                            logger.info('{} update tracker {}', entry.get('title'), new_url)
                if not modify:
                    entry.reject()

    def _get_site_name(self, tracker_url):
        re_object = re.search('(?<=//).*?(?=/)', tracker_url)
        if re_object:
            domain = re_object.group().split('.')
            if len(domain) > 1:
                return domain[len(domain) - 2]

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

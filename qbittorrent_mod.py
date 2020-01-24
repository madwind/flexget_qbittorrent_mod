import os
import sys
from datetime import datetime
from os import path

d = path.dirname(__file__)
sys.path.append(d)
from flexget.entry import Entry
from loguru import logger
from flexget import plugin
from flexget.event import event
from qbittorrent_client import QBittorrentClient

logger = logger.bind(name='qbittorrent_mod')


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
        client = QBittorrentClient(config)
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
                    'only_complete': {'type': 'boolean'},
                },
                'additionalProperties': False
            }
        ]
    }

    def prepare_config(self, config):
        config = QBittorrentModBase.prepare_config(self, config)
        config.setdefault('only_complete', False)
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)

        if not config['enabled']:
            return
        if not self.client:
            self.client = self.create_client(config)
        entries = []

        for torrent in self.client.get_torrents():
            entry = Entry(
                title=torrent['name'],
                url='',
                torrent_info_hash=torrent['hash'],
                content_size=torrent['size'] / (1024 * 1024),
            )
            for key, value in torrent.items():
                if key in ['added_on', 'completion_on', 'last_activity', 'seen_complete']:
                    entry['qbittorrent_' + key] = datetime.fromtimestamp(value)
                else:
                    entry['qbittorrent_' + key] = value
            entries.append(entry)
        return entries


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
                                    'skip_checking': {'type': 'string'},
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
                                    'delete_files': {'type': 'boolean'}
                                }
                            },
                            'resume': {
                                'type': 'object',
                                'properties': {
                                    'only_complete': {'type': 'boolean'}
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
        config = QBittorrentModBase.prepare_config(self, config)
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
        if len(config['action']) != 1:
            raise plugin.PluginError('There must be and only one action')
        # don't add when learning
        if task.options.learn:
            return
        if not config['enabled']:
            return
            # Do not run if there is nothing to do
        if not task.accepted:
            return
        if self.client is None:
            self.client = self.create_client(config)
            if self.client:
                logger.debug('Successfully connected to qBittorrent.')
            else:
                raise plugin.PluginError("Couldn't connect to qBittorrent.")

        if config['action'].get('add'):
            for entry in task.accepted:
                self.add_entries(task, entry, config)
                logger.info('qBittorrent: add {}', entry['title'])
        elif config['action'].get('remove'):
            session_torrents = self.client.get_torrents()
            self.remove_entries(task, session_torrents, config)
        elif config['action'].get('resume'):
            self.resume_entries(task, config)
        else:
            raise plugin.PluginError('Not connected.')

    def add_entries(self, task, entry, config):
        add_options = config['action']['add']

        add_options['autoTMM'] = entry.get('autoTMM', add_options.get('autoTMM'))
        add_options['category'] = entry.get('category', add_options.get('category'))
        add_options['savepath'] = entry.get('savepath', add_options.get('savepath'))
        add_options['paused'] = entry.get('paused', add_options.get('paused'))

        if add_options.get('autoTMM') and not add_options.get('category'):
            del add_options['savepath']

        if add_options.get('paused') is None:
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

    def remove_entries(self, task, session_torrents, config):
        remove_options = config['action']['remove']
        delete_files = remove_options.get('delete_files')
        check_reseed = remove_options.get('check_reseed')

        entry_map = {}
        task_torrent_hashes = set()
        # 构造需要删除的列表
        delete_hashes = set()

        # 获取所有entry
        for entry in task.entries:
            entry_map[entry['torrent_info_hash']] = entry
            if entry.accepted:
                task_torrent_hashes.add(entry['torrent_info_hash'])

        reseed_map = self.client.get_reseed_map()
        for task_torrent_hash in task_torrent_hashes:
            pieces_hashes = self.client.get_torrent_pieces_hashes(task_torrent_hash)
            client_torrent_reseed_list = reseed_map.get(pieces_hashes)
            torrent_hashes = set()
            for client_torrent in client_torrent_reseed_list:
                torrent_hashes.add(client_torrent['hash'])
            if check_reseed and not task_torrent_hashes >= torrent_hashes:
                continue
            else:
                delete_hashes.update(torrent_hashes)

        for torrent_hash, entry in entry_map.items():
            if torrent_hash in delete_hashes:
                entry.accept()
                logger.info('qBittorrent delete: {}', entry['title'])
            else:
                entry.reject()

        self.client.delete_torrents(str.join('|', delete_hashes), delete_files)

    def resume_entries(self, task, config):
        resume_options = config['action']['resume']
        only_complete = resume_options.get('only_complete')
        hashes = []
        for entry in task.accepted:
            hashes.append(entry['torrent_info_hash'])
            logger.info('qBittorrent: resume {}', entry['title'])
        self.client.resume_torrents(str.join('|', hashes))

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

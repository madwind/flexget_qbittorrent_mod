from __future__ import annotations

import copy
from datetime import datetime

from flexget import plugin
from flexget.entry import Entry
from flexget.task import Task
from loguru import logger

from ..client.qbittorrent_client import QBittorrentClientFactory, QBittorrentClient
from ..utils import net_utils
from .operations import QBittorrentOperationsMixin


class QBittorrentModBase:
    def __init__(self):
        self.client = None

    def prepare_config(self, config: dict) -> dict:
        if isinstance(config, bool):
            config = {'enabled': config}
        config.setdefault('enabled', True)
        config.setdefault('host', 'localhost')
        config.setdefault('port', 8080)
        config.setdefault('use_ssl', False)
        config.setdefault('verify_cert', True)
        return config

    def create_client(self, config: dict) -> QBittorrentClient:
        client = QBittorrentClientFactory().get_client(config)
        return client

    def on_task_start(self, task: Task, config: dict) -> None:
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
            'force_update': {'type': 'string', 'enum': ['uploading', 'active', 'all']},
            'enabled': {'type': 'boolean'},
        },
        'additionalProperties': False
    }

    def prepare_config(self, config: dict) -> dict:
        config = QBittorrentModBase.prepare_config(self, config)
        return config

    def on_task_input(self, task: Task, config: dict) -> list | None:
        config = self.prepare_config(config)
        if not config['enabled']:
            return None
        server_state = config.get('server_state')
        if server_state:
            entry = Entry(
                title='qBittorrent Server State' if isinstance(server_state, bool) else server_state,
                url=config.get('host')
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
            force_update = config.get('force_update', False)
            return list(
                self.client.get_main_data_snapshot(id(task), force_update=force_update).get('entry_dict').values())


class PluginQBittorrentMod(QBittorrentOperationsMixin, QBittorrentModBase):
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
                            'tags': {'type': 'string'},
                            'skip_checking': {'type': 'boolean'},
                            'paused': {'type': 'string'},
                            'root_folder': {'type': 'string'},
                            'rename': {'type': 'string'},
                            'upLimit': {'type': 'integer'},
                            'dlLimit': {'type': 'integer'},
                            'autoTMM': {'type': 'boolean'},
                            'sequentialDownload': {'type': 'string'},
                            'firstLastPiecePrio': {'type': 'string'},
                            'tracker_options': {
                                'type': 'object',
                                'properties': {
                                    'tag_by_tracker': {'type': 'boolean'},
                                    'specific_trackers:': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'additionalProperties': {
                                                'type': 'object',
                                                'properties': {
                                                    'savepath': {'type': 'string'},
                                                    'cookie': {'type': 'string'},
                                                    'category': {'type': 'string'},
                                                    'tags': {'type': 'string'},
                                                    'skip_checking': {'type': 'boolean'},
                                                    'paused': {'type': 'string'},
                                                    'root_folder': {'type': 'string'},
                                                    'rename': {'type': 'string'},
                                                    'upLimit': {'type': 'integer'},
                                                    'dlLimit': {'type': 'integer'},
                                                    'autoTMM': {'type': 'boolean'},
                                                    'sequentialDownload': {'type': 'string'},
                                                    'firstLastPiecePrio': {'type': 'string'},
                                                },
                                                'additionalProperties': False,
                                            },
                                            'maxProperties': 1,
                                        },
                                    }
                                }
                            },
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
                                    'dl_limit': {'oneOf': [{'type': 'boolean'}, {'type': 'integer'}]},
                                    'up_bandwidth_limit': {'type': 'integer'},
                                    'up_speed': {
                                        'oneOf': [
                                            {'type': 'boolean'},
                                            {'type': 'integer'},
                                            {'type': 'number', 'minimum': 0.1, 'maximum': 0.9},
                                        ]
                                    },
                                    'all': {'type': 'boolean'},
                                    'remember': {'type': 'boolean', 'default': True}
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
                            'modify_trackers': {
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
                    },
                    'limit_upload_by_tracker': {
                        'type': 'object',
                        'properties': {
                            'working': {'type': 'integer'},
                            'not_working': {'type': 'integer'}
                        }
                    },
                    'refresh_tracker': {
                        'type': 'boolean'
                    }
                },
                "minProperties": 1,
                "maxProperties": 1,
            },
            'fail_html': {'type': 'boolean'},
        },
        'additionalProperties': False
    }

    def prepare_config(self, config: dict) -> dict:
        config = super().prepare_config(config)
        config.setdefault('fail_html', True)
        return config

    @plugin.priority(120)
    def on_task_download(self, task: Task, config: dict) -> None:
        config = self.prepare_config(config)
        add_options = config.get('action', {}).get('add')
        if not add_options or not task.accepted:
            return

        if not self.client:
            self.client = self.create_client(config)
            if self.client:
                logger.debug('Successfully connected to qBittorrent.')
            else:
                raise plugin.PluginError("Couldn't connect to qBittorrent.")

        main_data_snapshot = self.client.get_main_data_snapshot(id(task))
        server_state = main_data_snapshot.get('server_state')

        reject_on = add_options.get('reject_on', {})
        remember_reject = reject_on.get('remember', True)
        bandwidth_limit = reject_on.get('bandwidth_limit')
        reject_on_dl_speed = reject_on.get('dl_speed')
        reject_on_dl_limit = reject_on.get('dl_limit')
        up_bandwidth_limit = reject_on.get('up_bandwidth_limit')
        reject_on_up_speed = reject_on.get('up_speed')
        reject_on_all = reject_on.get('all')
        reject_reason = ''

        up_rate_limit = server_state.get('up_rate_limit')
        dl_rate_limit = server_state.get('dl_rate_limit')

        if reject_on_up_speed:
            if isinstance(reject_on_up_speed, float):
                up_rate_limit = up_rate_limit if up_rate_limit else up_bandwidth_limit
                reject_on_up_speed = int(up_rate_limit * reject_on_up_speed)
            up_info_speed = server_state.get('up_info_speed')
            if up_info_speed and up_info_speed > reject_on_up_speed:
                reject_reason = 'up_speed: {:.2F} MiB > reject_on_up_speed: {:.2F} MiB'.format(
                    up_info_speed / (1024 * 1024), reject_on_up_speed / (1024 * 1024))

        if reject_on_dl_limit and dl_rate_limit and dl_rate_limit < reject_on_dl_limit:
            reject_reason = 'dl_limit: {:.2F} MiB < reject_on_dl_limit: {:.2F} MiB'.format(
                dl_rate_limit / (1024 * 1024), reject_on_dl_limit / (1024 * 1024))
        elif reject_on_dl_speed:
            if isinstance(reject_on_dl_speed, float):
                dl_rate_limit = dl_rate_limit if dl_rate_limit else bandwidth_limit
                reject_on_dl_speed = int(dl_rate_limit * reject_on_dl_speed)
            dl_info_speed = server_state.get('dl_info_speed')
            if dl_info_speed and dl_info_speed > reject_on_dl_speed:
                reject_reason = 'dl_speed: {:.2F} MiB > reject_on_dl_speed: {:.2F} MiB'.format(
                    dl_info_speed / (1024 * 1024), reject_on_dl_speed / (1024 * 1024))

        if reject_on_all:
            reject_reason = 'reject on all'

        if 'download' not in task.config:
            download = plugin.get('download', self)
        headers = copy.deepcopy(task.requests.headers)
        for entry in task.accepted:
            if reject_reason:
                entry.reject(reason=reject_reason, remember=remember_reject)
                site_name = net_utils.get_site_name(entry.get('url'))
                logger.info('reject {}, because: {}, site: {}', entry['title'], reject_reason, site_name)
                continue
            if entry.get('headers'):
                task.requests.headers.update(entry['headers'])
            else:
                task.requests.headers.clear()
                task.requests.headers = headers
            if entry.get('cookie'):
                task.requests.cookies.update(net_utils.cookie_str_to_dict(entry['cookie']))
            else:
                task.requests.cookies.clear()
            download.get_temp_file(task, entry, handle_magnets=True, fail_html=config['fail_html'])

    @plugin.priority(135)
    def on_task_output(self, task: Task, config: dict) -> None:
        config = self.prepare_config(config)
        action_config = config.get('action', {})
        if len(action_config) != 1:
            raise plugin.PluginError('There must be and only one action')
        # don't add when learning
        if task.options.learn or not (task.accepted or action_config.get('remove')):
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

    def on_task_learn(self, task: Task, config: dict) -> None:
        """ Make sure all temp files are cleaned up when entries are learned """
        # If download plugin is enabled, it will handle cleanup.
        if 'download' not in task.config:
            download = plugin.get('download', self)
            download.cleanup_temp_files(task)

    on_task_abort = on_task_learn


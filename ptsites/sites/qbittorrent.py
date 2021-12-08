from datetime import datetime

from loguru import logger

from ..client.qbittorrent_client import QBittorrentClient
from ..schema.site_base import SiteBase


class MainClass(SiteBase):

    def __init__(self):
        super().__init__()
        self.client = None

    @classmethod
    def build_sign_in_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'host': {'type': 'string'},
                        'port': {'type': 'integer'},
                        'use_ssl': {'type': 'boolean'},
                        'username': {'type': 'string'},
                        'password': {'type': 'string'}
                    },
                    'additionalProperties': False
                }
            }
        }

    @classmethod
    def build_reseed_schema(cls):
        return {}

    @classmethod
    def build_sign_in_entry(cls, entry, config):
        entry['site_name'] = entry['site_config'].get('name')
        entry['title'] = f"{entry['site_name']} {datetime.now().date()}"
        entry['do_not_count'] = True

    def sign_in(self, entry, config):
        site_config = self.prepare_config(entry['site_config'])
        try:
            if not self.client:
                self.client = self.create_client(site_config)
                entry['main_data_snapshot'] = self.client.get_main_data_snapshot(id(entry))
                entry['result'] = 'ok!'
        except Exception as e:
            entry.fail_with_prefix('error: {}'.format(e))

    def get_message(self, entry, config):
        pass

    def get_details(self, entry, config):
        server_state = entry['main_data_snapshot']['server_state']
        torrents = entry['main_data_snapshot']['entry_dict']
        details = {
            'downloaded': '{} B'.format(server_state['alltime_dl']),
            'uploaded': '{} B'.format(server_state['alltime_ul']),
            'share_ratio': server_state['global_ratio'],
            'points': 0,
            'leeching': len(
                list(filter(lambda torrent: ('dl' in torrent['qbittorrent_state'].lower() or 'downloading' in torrent[
                    'qbittorrent_state'].lower()) and 'pause' not in torrent['qbittorrent_state'],
                            torrents.values()))),
            'seeding': len(
                list(filter(lambda torrent: 'up' in torrent['qbittorrent_state'].lower() and 'pause' not in torrent[
                    'qbittorrent_state'],
                            torrents.values()))),
            'hr': 0
        }
        entry['details'] = details
        logger.info('site_name: {}, details: {}', entry['site_name'], entry['details'])

    def prepare_config(self, site_config):
        site_config.setdefault('enabled', True)
        site_config.setdefault('host', 'localhost')
        site_config.setdefault('port', 8080)
        site_config.setdefault('use_ssl', False)
        site_config.setdefault('verify_cert', True)
        return site_config

    def create_client(self, config):
        client = QBittorrentClient(config)
        return client

from datetime import datetime

from loguru import logger

from ..base.detail import Detail
from ..base.entry import SignInEntry
from ..base.sign_in import SignIn
from ..client.qbittorrent_client import QBittorrentClient
from ..utils.net_utils import get_module_name


class MainClass(SignIn, Detail):

    def __init__(self) -> None:
        super().__init__()
        self.client = None

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'host': {'type': 'string'},
                        'port': {'type': 'integer'},
                        'use_ssl': {'type': 'boolean'},
                        'username': {'type': 'string'},
                        'password': {'type': 'string'},
                        'verify_cert': {'type': 'boolean'}
                    },
                    'additionalProperties': False
                }
            }
        }

    @classmethod
    def sign_in_build_entry(cls, entry: SignInEntry, config: dict) -> None:
        entry['site_name'] = entry['site_config'].get('name')
        entry['title'] = f"{entry['site_name']} {datetime.now().date()}"
        entry['do_not_count'] = True

    def sign_in(self, entry: SignInEntry, config: dict) -> None:
        site_config = self.prepare_config(entry['site_config'])
        try:
            if not self.client:
                self.client = self.create_client(site_config)
                entry['main_data_snapshot'] = self.client.get_main_data_snapshot(id(entry))
                entry['result'] = 'ok!'
        except Exception as e:
            entry.fail_with_prefix(f'error: {e}')

    def get_details(self, entry: SignInEntry, config: dict) -> None:
        server_state = entry['main_data_snapshot']['server_state']
        torrents = entry['main_data_snapshot']['entry_dict']
        details = {
            'downloaded': f'{server_state["alltime_dl"]} B',
            'uploaded': f'{server_state["alltime_ul"]} B',
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

    def prepare_config(self, site_config: dict) -> dict:
        site_config.setdefault('enabled', True)
        site_config.setdefault('host', 'localhost')
        site_config.setdefault('port', 8080)
        site_config.setdefault('use_ssl', False)
        site_config.setdefault('verify_cert', True)
        return site_config

    def create_client(self, config: dict) -> QBittorrentClient:
        client = QBittorrentClient(config)
        return client

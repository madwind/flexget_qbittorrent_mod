from datetime import datetime

from loguru import logger

from ..client.qbittorrent_client import QBittorrentClient

'''
sign_in:
  qbittorrent:
    - <name>: <name>
      host: <host>
      port: <port>
      use_ssl: <use_ssl>
      username: <username>
      password: <password>
    - <name>: <name>
      host: <host>
      port: <port>
      use_ssl: <use_ssl>
      username: <username>
      password: <password>
'''


class MainClass:

    def __init__(self):
        self.client = None

    @staticmethod
    def build_sign_in_entry(entry, config):
        entry['site_name'] = entry['site_config'].get('name')
        entry['title'] = f"{entry['site_name']} {datetime.now().date()}"

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
        entry['do_not_count'] = True

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

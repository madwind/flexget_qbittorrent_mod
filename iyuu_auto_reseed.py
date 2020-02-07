import hashlib
import sys
import time
from json import JSONDecodeError
from os import path

import requests
from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.utils import json

d = path.dirname(__file__)
sys.path.append(d)
from qbittorrent_client import QBittorrentClientFactory


class PluginIYUUAutoReseed():
    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'iyuu': {'type': 'string'},
                    'version': {'type': 'string'},
                    'passkeys': {
                        'type': 'object',
                        'properties': {
                        }
                    },
                    'qbittorrent_ressed': {
                        'host': {'type': 'string'},
                        'use_ssl': {'type': 'boolean'},
                        'port': {'type': 'integer'},
                        'username': {'type': 'string'},
                        'password': {'type': 'string'},
                        'verify_cert': {'type': 'boolean'}
                    }
                },
                'additionalProperties': False
            }
        ]
    }

    def prepare_config(self, config):
        config.setdefault('iyuu', '')
        config.setdefault('version', '0.3.0')
        config.setdefault('passkeys', {})
        config.setdefault('qbittorrent_ressed', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        passkeys = config.get('passkeys')

        torrent_dict, torrents_hashes = self.get_torrents_data(task, config)
        try:
            response_json = requests.post('http://api.iyuu.cn/?service=App.Api.Reseed', json=torrents_hashes).json()
        except JSONDecodeError as e:
            raise plugin.PluginError(
                'Error when trying to send request to http://api.iyuu.cn/?service=App.Api.Reseed: {}'.format(e)
            )
        reseed_json = response_json['clients_0']
        sites_json = response_json['sites']

        entries = []
        if response_json:
            for info_hash, seeds_data in reseed_json.items():
                for torrent in seeds_data['torrent']:
                    site = sites_json[str(torrent['sid'])]
                    client_torrent = torrent_dict[info_hash]
                    base_url = site['base_url']
                    protocol = 'https'
                    site_name = ''
                    passkey = ''
                    for key, value in passkeys.items():
                        if key in base_url:
                            site_name = key
                            passkey = value
                            break
                    if not passkey:
                        continue
                    if site_name == 'totheglory':
                        download_page = site['download_page'].format(str(torrent['torrent_id']) + '/' + passkey)
                    else:
                        download_page = site['download_page'].format(str(torrent['torrent_id']) + '&passkey=' + passkey)
                    if site_name == 'oshen':
                        protocol = 'http'

                    entry = Entry(
                        title=client_torrent['title'],
                        url='{}://{}/{}'.format(protocol, base_url, download_page),
                        torrent_info_hash=torrent['info_hash']
                    )
                    entry['autoTMM'] = client_torrent['qbittorrent_auto_tmm']
                    entry['category'] = client_torrent['qbittorrent_category']
                    entry['savepath'] = client_torrent['qbittorrent_save_path']
                    entry['paused'] = 'true'
                    entries.append(entry)
        return entries

    def get_torrents_data(self, task, config):
        client = QBittorrentClientFactory().get_client(config.get('qbittorrent_ressed'))
        task_data = client.get_task_data(id(task))
        torrent_dict = {}
        torrents_hashes = {}
        hashes = []

        for entry in task_data.get('entry_dict').values():
            if 'up' in entry['qbittorrent_state'].lower():
                torrent_dict[entry['torrent_info_hash']] = entry
                hashes.append(entry['torrent_info_hash'])

        list.sort(hashes)
        hashes_json = json.dumps(hashes)
        sha1 = hashlib.sha1(hashes_json.encode("utf-8")).hexdigest()

        torrents_hashes['hash'] = {}
        torrents_hashes['hash']['clients_0'] = hashes_json
        torrents_hashes['sha1'] = []
        torrents_hashes['sha1'].append(sha1)
        torrents_hashes['sign'] = config['iyuu']
        torrents_hashes['version'] = config['version']
        torrents_hashes['timestamp'] = int(time.time())

        return torrent_dict, torrents_hashes


@event('plugin.register')
def register_plugin():
    plugin.register(PluginIYUUAutoReseed, 'iyuu_auto_reseed', api_ver=2)

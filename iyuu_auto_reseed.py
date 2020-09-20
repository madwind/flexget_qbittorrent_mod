import hashlib
import time
from json import JSONDecodeError

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.utils import json
from loguru import logger
from requests import RequestException

from .ptsites.executor import Executor


class PluginIYUUAutoReseed():
    schema = {
        'type': 'object',
        'properties': {
            'iyuu': {'type': 'string'},
            'version': {'type': 'string'},
            'limit': {'type': 'integer'},
            'passkeys': {
                'type': 'object',
                'properties': {
                }
            }
        },
        'additionalProperties': False
    }

    def prepare_config(self, config):
        config.setdefault('iyuu', '')
        config.setdefault('version', '1.10.6')
        config.setdefault('passkeys', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        passkeys = config.get('passkeys')
        limit = config.get('limit', 1)

        torrent_dict, torrents_hashes = self.get_torrents_data(task, config)
        try:
            response_json = task.requests.post('http://api.iyuu.cn/?service=App.Api.Reseed',
                                               json=torrents_hashes, timeout=60).json()
        except (RequestException, JSONDecodeError) as e:
            raise plugin.PluginError(
                'Error when trying to send request to http://api.iyuu.cn/?service=App.Api.Reseed: {}'.format(e)
            )
        if response_json.get('ret') != 200:
            raise plugin.PluginError(
                'http://api.iyuu.cn/?service=App.Api.Reseed Error: {}'.format(response_json)
            )
        reseed_json = response_json['data']['clients_0']
        sites_json = response_json['data']['sites']

        entries = []
        site_limit = {}
        if response_json and not isinstance(reseed_json, list):
            for info_hash, seeds_data in reseed_json.items():
                for torrent in seeds_data['torrent']:
                    site = sites_json.get(str(torrent['sid']))
                    if not site:
                        continue
                    client_torrent = torrent_dict[info_hash]
                    base_url = site['base_url'] if site['base_url'] != 'pt.upxin.net' else 'pt.hdupt.com'

                    site_name = ''
                    passkey = ''
                    for key, value in passkeys.items():
                        if key in base_url:
                            site_name = key
                            passkey = value
                            break
                    if not passkey:
                        continue
                    if not site_limit.get(site_name):
                        site_limit[site_name] = 1
                    else:
                        if site_limit[site_name] >= limit:
                            continue
                        site_limit[site_name] = site_limit[site_name] + 1
                    site['download_page'] = site['download_page'].replace('{}', '{torrent_id}')
                    torrent_id = str(torrent['torrent_id'])

                    entry = Entry(
                        title=client_torrent['title'],
                        torrent_info_hash=torrent['info_hash']
                    )

                    entry['autoTMM'] = client_torrent['qbittorrent_auto_tmm']
                    entry['category'] = client_torrent['qbittorrent_category']
                    entry['savepath'] = client_torrent['qbittorrent_save_path']
                    entry['paused'] = 'true'
                    Executor.build_reseed_entry(entry, base_url, site, site_name, passkey, torrent_id)
                    entries.append(entry)
        return entries

    def get_torrents_data(self, task, config):
        torrent_dict = {}
        torrents_hashes = {}
        hashes = []

        for entry in task.all_entries:
            entry.reject('torrent form client')
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

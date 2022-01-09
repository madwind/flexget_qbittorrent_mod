import hashlib
import time
from enum import Enum
from json import JSONDecodeError

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.utils import json
from loguru import logger
from requests import RequestException

from .ptsites.executor import Executor


class ClientType(Enum):
    qBittorrent = 'qBittorrent'
    Transmission = 'Transmission'


class PluginIYUUAutoReseed:
    schema = {
        'type': 'object',
        'properties': {
            'iyuu': {'type': 'string'},
            'user-agent': {'type': 'string'},
            'show_detail': {'type': 'boolean'},
            'limit': {'type': 'integer'},
            'passkeys': {
                'type': 'object',
                'properties': Executor.build_reseed_schema()
            }
        },
        'additionalProperties': False
    }

    def prepare_config(self, config):
        config.setdefault('iyuu', '')
        config.setdefault('version', '1.10.9')
        config.setdefault('limit', 999)
        config.setdefault('show_detail', False)
        config.setdefault('passkeys', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        passkeys = config.get('passkeys')
        limit = config.get('limit')
        show_detail = config.get('show_detail')

        torrent_dict, torrents_hashes, client_type = self.get_torrents_data(task, config)
        if not torrents_hashes:
            return torrents_hashes
        try:
            data = {
                'sign': config['iyuu'],
                'version': config['version']
            }
            sites_response = task.requests.get('http://api.iyuu.cn/index.php?s=App.Api.Sites', timeout=60,
                                               params=data).json()
            if sites_response.get('ret') != 200:
                raise plugin.PluginError(
                    'http://api.iyuu.cn/index.php?s=App.Api.Sites: {}'.format(sites_response)
                )
            sites_json = self.modify_sites(sites_response['data']['sites'])

            reseed_response = task.requests.post('http://api.iyuu.cn/index.php?s=App.Api.Infohash',
                                                 json=torrents_hashes,
                                                 timeout=60).json()
            if reseed_response.get('ret') != 200:
                raise plugin.PluginError(
                    'http://api.iyuu.cn/index.php?s=App.Api.Infohash Error: {}'.format(reseed_response)
                )
            reseed_json = reseed_response['data']
        except (RequestException, JSONDecodeError) as e:
            raise plugin.PluginError(
                'Error when trying to send request to iyuu: {}'.format(e)
            )

        entries = []
        site_limit = {}
        if sites_json and reseed_json:
            for info_hash, seeds_data in reseed_json.items():
                client_torrent = torrent_dict[info_hash]
                for torrent in seeds_data['torrent']:
                    site = sites_json.get(str(torrent['sid']))
                    if not site:
                        continue
                    if torrent['info_hash'] in torrent_dict.keys():
                        continue
                    site_name = self._get_site_name(site['base_url'])
                    passkey = passkeys.get(site_name)
                    if not passkey:
                        if show_detail:
                            logger.info(
                                'no passkey, skip site: {}, title: {}'.format(site_name, client_torrent['title']))
                        continue
                    if not site_limit.get(site_name):
                        site_limit[site_name] = 1
                    else:
                        if site_limit[site_name] >= limit:
                            logger.info(
                                'site_limit:{} >= limit: {}, skip site: {}, title: {}'.format(
                                    site_limit[site_name],
                                    limit,
                                    site_name,
                                    client_torrent['title'])
                            )
                            continue
                        site_limit[site_name] = site_limit[site_name] + 1
                    torrent_id = str(torrent['torrent_id'])
                    entry = Entry(
                        title=client_torrent['title'],
                        torrent_info_hash=torrent['info_hash']
                    )
                    if client_type == ClientType.qBittorrent:
                        entry['autoTMM'] = client_torrent['qbittorrent_auto_tmm']
                        entry['category'] = client_torrent['qbittorrent_category']
                        entry['savepath'] = client_torrent['qbittorrent_save_path']
                        entry['paused'] = 'true'
                    elif client_type == ClientType.Transmission:
                        entry['path'] = client_torrent['transmission_downloadDir']
                        entry['add_paused'] = 'Yes'
                    entry['class_name'] = site_name
                    Executor.build_reseed(entry, config, site, passkey, torrent_id)
                    if show_detail:
                        logger.info(
                            f"accept site: {site_name}, title: {client_torrent['title']}, url: {entry.get('url', None)}")
                    if entry.get('url'):
                        entries.append(entry)
        return entries

    def get_torrents_data(self, task, config):
        torrent_dict = {}
        torrents_hashes = {}
        hashes = []
        client_type = ''

        if task.all_entries:
            if task.all_entries[0].get('qbittorrent_state'):
                client_type = ClientType.qBittorrent
            elif task.all_entries[0].get('transmission_status'):
                client_type = ClientType.Transmission

        for entry in task.all_entries:
            entry.reject('torrent form client')
            if client_type == ClientType.qBittorrent:
                self.get_qbittorrent_seeding(entry, torrent_dict, hashes)
            elif client_type == ClientType.Transmission:
                self.get_transmission_seeding(entry, torrent_dict, hashes)

        list.sort(hashes)
        hashes_json = json.dumps(hashes, separators=(',', ':'))
        sha1 = hashlib.sha1(hashes_json.encode("utf-8")).hexdigest()

        torrents_hashes['hash'] = hashes_json
        torrents_hashes['sha1'] = sha1

        torrents_hashes['sign'] = config['iyuu']
        torrents_hashes['timestamp'] = int(time.time())
        torrents_hashes['version'] = config['version']

        return torrent_dict, torrents_hashes, client_type

    def modify_sites(self, sites_json):
        sites_dict = {}
        for site in sites_json:
            site['download_page'] = site['download_page'].replace('{}', '{torrent_id}')
            if site['base_url'] == 'pt.upxin.net':
                site['base_url'] = 'pt.hdupt.com'
            sites_dict[str(site['id'])] = site
        return sites_dict

    def _get_site_name(self, base_url):
        domain = base_url.split('.')
        site_name = domain[-2]
        if site_name == 'edu':
            site_name = domain[-3]
        return site_name

    def get_qbittorrent_seeding(self, entry, torrent_dict, hashes):
        if 'up' in entry['qbittorrent_state'].lower() and 'pause' not in entry['qbittorrent_state'].lower():
            torrent_dict[entry['torrent_info_hash']] = entry
            hashes.append(entry['torrent_info_hash'])

    def get_transmission_seeding(self, entry, torrent_dict, hashes):
        if 'seed' in entry['transmission_status'].lower():
            torrent_dict[entry['torrent_info_hash']] = entry
            hashes.append(entry['torrent_info_hash'])


@event('plugin.register')
def register_plugin():
    plugin.register(PluginIYUUAutoReseed, 'iyuu_auto_reseed', api_ver=2)

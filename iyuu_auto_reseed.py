from __future__ import annotations

import copy
import hashlib
import time
from json import JSONDecodeError
from urllib.parse import urljoin

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.plugins.clients.deluge import OutputDeluge
from flexget.plugins.clients.transmission import PluginTransmission
from flexget.task import Task
from flexget.utils import json
from loguru import logger
from requests import RequestException

from .ptsites import executor
from .ptsites.utils import net_utils


def update_header_cookie(entry: Entry, headers: dict, task: Task) -> None:
    if entry.get('headers'):
        task.requests.headers.update(entry['headers'])
    else:
        task.requests.headers.clear()
        task.requests.headers = headers
    if entry.get('cookie'):
        task.requests.cookies.update(net_utils.cookie_str_to_dict(entry['cookie']))
    else:
        task.requests.cookies.clear()


def get_qbittorrent_mod_seeding(client_torrent: dict) -> bool | None:
    if 'up' in client_torrent['qbittorrent_state'].lower() and 'pause' not in client_torrent[
        'qbittorrent_state'].lower():
        client_torrent['reseed'] = {
            'path': client_torrent['qbittorrent_save_path'],
            'autoTMM': client_torrent['qbittorrent_auto_tmm'],
            'category': client_torrent['qbittorrent_category']
        }
        return True
    return None


def to_qbittorrent_mod(entry: Entry, client_torrent: dict) -> None:
    entry['savepath'] = client_torrent['reseed'].get('path')
    entry['autoTMM'] = client_torrent['reseed'].get('autoTMM')
    entry['category'] = client_torrent['reseed'].get('category')
    entry['paused'] = 'true'


def get_transmission_seeding(client_torrent: dict) -> dict | None:
    if 'seed' in client_torrent['transmission_status'].lower():
        client_torrent['reseed'] = {
            'path': client_torrent['transmission_downloadDir']
        }
        return client_torrent
    return None


def to_transmission(entry: Entry, client_torrent: dict) -> None:
    entry['path'] = client_torrent['reseed'].get('path')
    entry['add_paused'] = 'Yes'


def transmission_on_task_download(self, task: Task, config: dict) -> None:
    config = self.prepare_config(config)
    if not config['enabled']:
        return
    if 'download' not in task.config:
        download = plugin.get('download', self)
        headers = copy.deepcopy(task.requests.headers)
        for entry in task.accepted:
            if entry.get('transmission_id'):
                continue
            if config['action'] != 'add' and entry.get('torrent_info_hash'):
                continue
            update_header_cookie(entry, headers, task)
            download.get_temp_file(task, entry, handle_magnets=True, fail_html=True)


PluginTransmission.on_task_download = transmission_on_task_download


def get_deluge_seeding(client_torrent: dict):
    if 'seeding' in client_torrent['deluge_state'].lower():
        client_torrent['reseed'] = {
            'path': client_torrent['deluge_save_path'],
            'move_completed_path': client_torrent['deluge_move_completed_path'],
        }
        return client_torrent


def to_deluge(entry: Entry, client_torrent: dict) -> None:
    entry['path'] = client_torrent['reseed'].get('path')
    entry['move_completed_path'] = client_torrent['reseed'].get('move_completed_path')
    entry['add_paused'] = 'Yes'


def deluge_on_task_download(self, task: Task, config: dict) -> None:
    config = self.prepare_config(config)
    if not config['enabled']:
        return
    if 'download' not in task.config:
        download = plugin.get('download', self)
        headers = copy.deepcopy(task.requests.headers)
        for entry in task.accepted:
            if entry.get('deluge_id'):
                continue
            if config['action'] != 'add' and entry.get('torrent_info_hash'):
                continue
            update_header_cookie(entry, headers, task)
            download.get_temp_file(task, entry, handle_magnets=True)


OutputDeluge.on_task_download = deluge_on_task_download

client_map = {
    'from_qbittorrent_mod': get_qbittorrent_mod_seeding,
    'qbittorrent_mod': to_qbittorrent_mod,
    'from_transmission': get_transmission_seeding,
    'transmission': to_transmission,
    'from_deluge': get_deluge_seeding,
    'deluge': to_deluge,
}


class PluginIYUUAutoReseed:
    schema = {
        'type': 'object',
        'properties': {
            'from': {
                'anyOf': [
                    {'$ref': '/schema/plugins?name=from_qbittorrent_mod'},
                    {'$ref': '/schema/plugins?name=from_transmission'},
                    {'$ref': '/schema/plugins?name=from_deluge'},
                ]
            },
            'to': {'type': 'string', 'enum': list(filter(lambda x: not x.startswith('from'), client_map.keys()))},
            'iyuu': {'type': 'string'},
            'user-agent': {'type': 'string'},
            'show_detail': {'type': 'boolean'},
            'limit': {'type': 'integer'},
            'passkeys': {
                'type': 'object',
                'properties': executor.build_reseed_schema()
            }
        },
        'additionalProperties': False
    }

    def prepare_config(self, config: dict) -> dict:
        config.setdefault('iyuu', '')
        config.setdefault('version', '1.10.9')
        config.setdefault('limit', 999)
        config.setdefault('show_detail', False)
        config.setdefault('passkeys', {})
        return config

    def on_task_input(self, task: Task, config: dict) -> list[Entry]:
        url = 'http://api.bolahg.cn'
        config = self.prepare_config(config)
        passkeys = config.get('passkeys')
        limit = config.get('limit')
        show_detail = config.get('show_detail')
        to = config.get('to')

        result = []
        from_client_method = None
        to_client_method = None

        for from_name, client_config in config['from'].items():
            from_client = plugin.get_plugin_by_name(from_name)
            start_method = from_client.phase_handlers['start']
            input_method = from_client.phase_handlers['input']
            if not to:
                to = from_name[5:]
            start_method(task, client_config)
            result = input_method(task, client_config)
            from_client_method = client_map[from_name]
            to_client_method = client_map[to]

        torrent_dict, torrents_hashes = self.get_torrents_data(result, config, from_client_method)

        if not torrent_dict:
            return []

        try:
            data = {
                'sign': config['iyuu'],
                'version': config['version']
            }
            sites_response = task.requests.get(urljoin(url, '/index.php?s=App.Api.Sites'), timeout=60,
                                               params=data).json()
            if sites_response.get('ret') != 200:
                raise plugin.PluginError(
                    f'{urljoin(url, "/index.php?s=App.Api.Sites")}: {sites_response}'
                )
            sites_json = self.modify_sites(sites_response['data']['sites'])

            reseed_response = task.requests.post(urljoin(url, '/index.php?s=App.Api.Infohash'),
                                                 json=torrents_hashes,
                                                 timeout=60).json()
            if reseed_response.get('ret') != 200:
                raise plugin.PluginError(
                    f'{urljoin(url, "/index.php?s=App.Api.Infohash")} Error: {reseed_response}'
                )
            reseed_json = reseed_response['data']
        except (RequestException, JSONDecodeError) as e:
            raise plugin.PluginError(
                f'Error when trying to send request to iyuu: {e}'
            )

        entries = []
        site_limit = {}
        if sites_json and reseed_json:
            for info_hash, seeds_data in reseed_json.items():
                client_torrent = torrent_dict[info_hash]
                for torrent in seeds_data['torrent']:
                    if not (site := sites_json.get(str(torrent['sid']))):
                        continue
                    if torrent['info_hash'] in torrent_dict.keys():
                        continue
                    site_name = self._get_site_name(site['base_url'])
                    passkey = passkeys.get(site_name)
                    if not passkey:
                        if show_detail:
                            logger.info(
                                f"no passkey, skip site: {site['base_url']}, title: {client_torrent['title']}")
                        continue
                    if not site_limit.get(site_name):
                        site_limit[site_name] = 1
                    else:
                        if site_limit[site_name] >= limit:
                            logger.info(
                                f'site_limit:{site_limit[site_name]} >= limit: {limit}, skip site: {site_name}, title: {client_torrent["title"]}'
                            )
                            continue
                        site_limit[site_name] = site_limit[site_name] + 1
                    torrent_id = str(torrent['torrent_id'])
                    entry = Entry(
                        title=client_torrent['title'],
                        torrent_info_hash=torrent['info_hash']
                    )
                    to_client_method(entry, client_torrent)
                    entry['class_name'] = site_name
                    executor.build_reseed_entry(entry, config, site, passkey, torrent_id)
                    if show_detail:
                        logger.info(
                            f"accept site: {site_name}, title: {client_torrent['title']}, url: {entry.get('url', None)}")
                    if entry.get('url'):
                        entries.append(entry)
        return entries

    def get_torrents_data(self, result: list, config: dict, from_client_method: callable) -> tuple[dict, dict]:
        torrent_dict = {}
        torrents_hashes = {}
        hashes = []

        for client_torrent in result:
            if from_client_method(client_torrent):
                torrent_info_hash = client_torrent['torrent_info_hash'].lower()
                torrent_dict[torrent_info_hash] = client_torrent
                hashes.append(torrent_info_hash)

        list.sort(hashes)
        hashes_json = json.dumps(hashes, separators=(',', ':'))
        sha1 = hashlib.sha1(hashes_json.encode("utf-8")).hexdigest()

        torrents_hashes['hash'] = hashes_json
        torrents_hashes['sha1'] = sha1

        torrents_hashes['sign'] = config['iyuu']
        torrents_hashes['timestamp'] = int(time.time())
        torrents_hashes['version'] = config['version']

        return torrent_dict, torrents_hashes

    def modify_sites(self, sites_json: list) -> dict[str, dict]:
        sites_dict = {}
        for site in sites_json:
            site['download_page'] = site['download_page'].replace('{}', '{torrent_id}')
            if site['base_url'] == 'pt.upxin.net':
                site['base_url'] = 'pt.hdupt.com'
            sites_dict[str(site['id'])] = site
        return sites_dict

    def _get_site_name(self, base_url: str) -> str:
        domain = base_url.split('.')
        site_name = domain[-2]
        return site_name if site_name != 'edu' else domain[-3]


@event('plugin.register')
def register_plugin() -> None:
    plugin.register(PluginIYUUAutoReseed, 'iyuu_auto_reseed', api_ver=2)

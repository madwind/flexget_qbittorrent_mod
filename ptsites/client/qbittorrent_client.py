from __future__ import annotations

import copy
import os
import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from json import JSONDecodeError
from typing import TypeVar

from flexget import plugin
from flexget.entry import Entry
from loguru import logger
from requests import RequestException, Session, Response

logger = logger.bind(name='qbittorrent_client')

T = TypeVar('T')


def singleton(cls: type[T]) -> Callable[..., T]:
    instances: dict[type[T], T] = {}

    def getinstance(*args, **kwargs) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return getinstance


@singleton
class QBittorrentClientFactory:
    _client_lock = threading.Lock()

    def __init__(self) -> None:
        self.client_map: dict[str, QBittorrentClient] = {}

    def get_client(self, config: dict) -> QBittorrentClient:
        client_key = f"{config.get('host')}{config.get('port')}"
        client = self.client_map.get(client_key)
        if not client:
            with self._client_lock:
                if not client:
                    client = QBittorrentClient(config)
                    self.client_map[client_key] = client
        return client


class QBittorrentClient:
    API_URL_LOGIN = '/api/v2/auth/login'
    API_URL_ADD_NEW_TORRENT = '/api/v2/torrents/add'
    API_URL_ADD_TORRENT_TAGS = '/api/v2/torrents/addTags'

    API_URL_SET_APPLICATION_PREFERENCES = '/api/v2/app/setPreferences'
    API_URL_SET_TORRENT_UPLOAD_LIMIT = '/api/v2/torrents/setUploadLimit'
    API_URL_RESUME = '/api/v2/torrents/resume'
    API_URL_PAUSE = '/api/v2/torrents/pause'
    API_URL_RECHECK_TORRENTS = '/api/v2/torrents/recheck'
    API_URL_EDIT_TRACKERS = '/api/v2/torrents/editTracker'
    API_URL_REMOVE_TRACKERS = '/api/v2/torrents/removeTrackers'
    API_URL_DELETE_TORRENTS = '/api/v2/torrents/delete'

    API_URL_GET_MAIN_DATA = '/api/v2/sync/maindata'
    API_URL_GET_APPLICATION_PREFERENCES = '/api/v2/app/preferences'
    API_URL_GET_TORRENT_LIST = '/api/v2/torrents/info'
    API_URL_GET_TORRENT_GENERIC_PROPERTIES = '/api/v2/torrents/properties'
    API_URL_GET_TORRENT_PIECES_STATES = '/api/v2/torrents/pieceHashes'
    API_URL_GET_TORRENT_TRACKERS = '/api/v2/torrents/trackers'

    build_entry_lock = threading.Lock()

    def __init__(self, config) -> None:
        self.session = None
        self._verify = True
        self.url = ''
        self.connected = False
        self._reseed_dict = {}
        self._entry_dict = {}
        self._server_state = {}
        self._action_history = {}
        self._rid = 0
        self._torrent_attr_len = 0
        self._task_dict = {}
        self._config = config
        self.connect()

    def _request(self, method: str, url: str, msg_on_fail: str | None = None, **kwargs) -> Response:
        if not url.endswith(self.API_URL_LOGIN) and not self.connected:
            self.connected = False
            self.reset_rid(reason='not connected')
            self.connect()
        try:
            response = self.session.request(method, url, timeout=60, **kwargs)
            if response.status_code == 403 or (self.API_URL_LOGIN in url and response.text == 'Fails.'):
                msg = (
                    f'Failure. URL: {url}, data: {kwargs}, status_code: {response.status_code}'
                    if not msg_on_fail
                    else msg_on_fail
                )
                self.connected = False
                self.reset_rid(reason='response error')
            else:
                return response
        except RequestException as e:
            self.reset_rid(reason='RequestException')
            msg = str(e)
        raise plugin.PluginError(f'Error when trying to send request to qbittorrent: {msg}')

    def check_api_version(self, msg_on_fail: str) -> None:
        try:
            url = self.url + "/api/v2/app/webapiVersion"
            response = self.session.request('get', url, verify=self._verify)
            if response.status_code != 404:
                return response
            msg = f'Failure. URL: {url}' if not msg_on_fail else msg_on_fail
        except RequestException as e:
            msg = str(e)
        raise plugin.PluginError(f'Error when trying to send request to qbittorrent: {msg}')

    def connect(self) -> None:
        """
        Connect to qBittorrent Web UI. Username and password not necessary
        if 'Bypass authentication for localhost' is checked and host is
        'localhost'.
        """
        self.session = Session()
        self._verify = self._config.get('verify_cert', True)

        self.url = f"{'https' if self._config['use_ssl'] else 'http'}://{self._config['host']}:{self._config['port']}"
        self.check_api_version('Check API version failed.')
        if self._config.get('username') and self._config.get('password'):
            data = {'username': self._config['username'], 'password': self._config['password']}
            response = self._request(
                'post',
                self.url + self.API_URL_LOGIN,
                data=data,
                msg_on_fail='Authentication failed.',
                verify=self._verify,
            )
            logger.info('Successfully connected to qbittorrent')
            self.connected = True

    def add_torrent_file(self, file_path: str, data: dict) -> None:
        multipart_data = {k: (None, v) for k, v in data.items()}
        with open(file_path, 'rb') as f:
            multipart_data['torrents'] = f
            response = self._request(
                'post',
                self.url + self.API_URL_ADD_NEW_TORRENT,
                msg_on_fail='add_torrent_file failed.',
                files=multipart_data,
                verify=self._verify,
            )
        logger.debug('add_torrent_file response: {}', response.content)

    def add_torrent_url(self, url: str, data: dict) -> None:
        data['urls'] = url
        multipart_data = {k: (None, v) for k, v in data.items()}
        self._request(
            'post',
            self.url + self.API_URL_ADD_NEW_TORRENT,
            msg_on_fail='add_torrent_url failed.',
            files=multipart_data,
            verify=self._verify,
        )

    def delete_torrents(self, hashes: str, delete_files) -> None:
        data = {'hashes': hashes, 'deleteFiles': delete_files}
        self._request(
            'post',
            self.url + self.API_URL_DELETE_TORRENTS,
            data=data,
            msg_on_fail='delete_torrents failed.',
            verify=self._verify,
        )
        self._check_action('delete_torrents', hashes)

    def recheck_torrents(self, hashes: str) -> None:
        data = {'hashes': hashes}
        self._request(
            'post',
            self.url + self.API_URL_RECHECK_TORRENTS,
            data=data,
            msg_on_fail='recheck_torrents failed.',
            verify=self._verify,
        )
        self._check_action('recheck_torrents', hashes)

    def get_torrent_generic_properties(self, torrent_hash) -> dict:
        data = {'hash': torrent_hash}
        return self._request(
            'get',
            self.url + self.API_URL_GET_TORRENT_GENERIC_PROPERTIES,
            params=data,
            msg_on_fail='get_torrent_generic_properties failed.',
            verify=self._verify,
        ).json()

    def get_torrent_trackers(self, torrent_hash) -> dict:
        data = {'hash': torrent_hash}
        response = self._request(
            'get',
            self.url + self.API_URL_GET_TORRENT_TRACKERS,
            params=data,
            msg_on_fail='get_torrent_trackers failed.',
            verify=self._verify
        )
        return response.json()

    def resume_torrents(self, hashes: str) -> None:
        data = {'hashes': hashes}
        self._request(
            'post',
            self.url + self.API_URL_RESUME,
            data=data,
            msg_on_fail='resume_torrents failed.',
            verify=self._verify,
        )
        self._check_action('resume_torrents', hashes)

    def pause_torrents(self, hashes: str) -> None:
        data = {'hashes': hashes}
        self._request(
            'post',
            self.url + self.API_URL_PAUSE,
            data=data,
            msg_on_fail='pause_torrents failed.',
            verify=self._verify,
        )
        self._check_action('pause_torrents', hashes)

    def edit_trackers(self, torrent_hash: str, origurl: str, newurl: str) -> None:
        data = {'hash': torrent_hash, 'origUrl': origurl, 'newUrl': newurl}
        response = self._request(
            'post',
            self.url + self.API_URL_EDIT_TRACKERS,
            data=data,
            msg_on_fail='edit_trackers failed.',
            verify=self._verify,
        )
        if response.status_code == 200:
            self._update_entry_trackers(torrent_hash)

    def remove_trackers(self, torrent_hash: str, urls: str) -> None:
        data = {'hash': torrent_hash, 'urls': urls}
        response = self._request(
            'post',
            self.url + self.API_URL_REMOVE_TRACKERS,
            data=data,
            msg_on_fail='remove_trackers failed.',
            verify=self._verify,
        )
        if response.status_code == 200:
            self._update_entry_trackers(torrent_hash)
        self._check_action('edit_trackers', torrent_hash)

    def add_torrent_tags(self, hashes: str, tags: str) -> None:
        data = {'hashes': hashes, 'tags': tags}
        if self._check_action('add_torrent_tags', hashes):
            self._request(
                'post',
                self.url + self.API_URL_ADD_TORRENT_TAGS,
                data=data,
                msg_on_fail='add_torrent_tags failed.',
                verify=self._verify,
            )

    def get_main_data(self) -> dict:
        data = {'rid': self._rid}
        try:
            main_data = self._request(
                'get',
                self.url + self.API_URL_GET_MAIN_DATA,
                params=data,
                msg_on_fail='get_main_data failed.',
                verify=self._verify,
            ).json()
            return main_data
        except JSONDecodeError as e:
            logger.debug(f'get_main_data: {e}')
            self.reset_rid(reason='get_main_data JSONDecodeError')
        raise plugin.PluginError('get_main_data failed.')

    def get_application_preferences(self) -> dict:
        return self._request(
            'get',
            self.url + self.API_URL_GET_APPLICATION_PREFERENCES,
            msg_on_fail='get_application_preferences failed.',
            verify=self._verify,
        ).json()

    def set_application_preferences(self, data: str) -> None:
        data = {'json': data}
        self._request(
            'post',
            self.url + self.API_URL_SET_APPLICATION_PREFERENCES,
            data=data,
            msg_on_fail='set_application_preferences failed.',
            verify=self._verify,
        )

    def set_torrent_upload_limit(self, hashes: str, limit) -> None:
        data = {'hashes': hashes, 'limit': limit}
        self._request(
            'post',
            self.url + self.API_URL_SET_TORRENT_UPLOAD_LIMIT,
            data=data,
            msg_on_fail='set_torrent_upload_limit failed.',
            verify=self._verify,
        )

    def get_main_data_snapshot(self, task_id: int, force_update=False):
        if not self._task_dict.get(task_id):
            with self.build_entry_lock:
                if not self._task_dict.get(task_id):
                    self._build_entry(force_update)
                    self._task_dict.clear()
                    self._task_dict[task_id] = {'server_state': copy.deepcopy(self._server_state),
                                                'entry_dict': copy.deepcopy(self._entry_dict),
                                                'reseed_dict': copy.deepcopy(self._reseed_dict)}
        return self._task_dict.get(task_id)

    def reset_rid(self, reason: str = 'unknown') -> None:
        self._rid = 0
        logger.warning(f'Sync error, reset rid. reason: {reason}')

    def _build_entry(self, force_update) -> None:
        self._building = True
        main_data = self.get_main_data()
        self._rid = main_data.get('rid')
        if is_new_data := main_data.get('full_update'):
            self._entry_dict = {}
            self._reseed_dict = {}
            self._action_history = {}
            self._last_update_time = datetime.now()

        if server_state := main_data.get('server_state'):
            for state, value in server_state.items():
                self._server_state[state] = value

        if torrents := main_data.get('torrents'):
            values = list(torrents.values())
            values_len = len(values)
            if is_new_data and values_len > 0:
                self._torrent_attr_len = len(values[0])
                logger.info('build_entry: building {} entries', values_len)
            for torrent_hash, torrent in torrents.items():
                self._update_entry(torrent_hash, torrent)
        if torrent_removed := main_data.get('torrents_removed'):
            for torrent_hash in torrent_removed:
                self._remove_torrent(torrent_hash)

        update_addition_flag = self._last_update_time < datetime.now() - timedelta(hours=1)
        if update_addition_flag or force_update:
            if force_update == 'active':
                for torrent_hash, entry in self._entry_dict.items():
                    if entry['qbittorrent_dlspeed'] or entry['qbittorrent_upspeed'] or entry[
                        'qbittorrent_up_limit'] == 1:
                        self._update_entry_trackers(torrent_hash)
            elif force_update == 'uploading':
                for torrent_hash, entry in self._entry_dict.items():
                    if entry['qbittorrent_upspeed'] or entry['qbittorrent_up_limit'] == 1:
                        self._update_entry_trackers(torrent_hash)
            else:
                self._last_update_time = datetime.now()
                for torrent_hash, entry in self._entry_dict.items():
                    self._update_addition(entry)
                    self._update_entry_trackers(torrent_hash)
        if is_new_data:
            logger.info('build_entry: build completion')

    def _update_entry(self, torrent_hash: str, torrent: dict) -> None:
        is_new_entry = False
        if not (entry := self._entry_dict.get(torrent_hash)):
            is_new_entry = True
            if len(torrent) != self._torrent_attr_len:
                self.reset_rid(reason='torrent lose attr')
                return
            save_path = self.save_path_suffix(torrent['save_path'])
            name = torrent['name']
            save_path_with_name = f'{save_path}{name}'
            torrent['save_path_with_name'] = save_path_with_name
            entry = Entry(
                title=name,
                url=torrent['magnet_uri'],
                path=save_path,
                torrent_info_hash=torrent_hash,
                content_size=torrent['size']
            )
            self._update_addition(entry)
            self._entry_dict[torrent_hash] = entry
            if not self._reseed_dict.get(save_path_with_name):
                self._reseed_dict[save_path_with_name] = []
            self._reseed_dict[save_path_with_name].append(entry)
        time_changed = False
        for key, value in torrent.items():
            if not is_new_entry:
                if key == 'save_path' and entry['qbittorrent_save_path'] != self.save_path_suffix(value):
                    self.reset_rid('save_path changed')
                if key == 'name' and entry['qbittorrent_name'] != value:
                    self.reset_rid('name changed')
            if key in ['added_on', 'completion_on', 'last_activity']:
                time_changed = True
            if key in ['added_on', 'completion_on', 'last_activity', 'seen_complete']:
                timestamp = value if value > 0 else 0
                entry['qbittorrent_' + key] = datetime.fromtimestamp(timestamp)
            else:
                entry['qbittorrent_' + key] = value
                if key in ['tracker']:
                    self._update_entry_trackers(torrent_hash)
        if time_changed:
            self._update_entry_last_activity(entry)
            self._update_reseed_addition(self._reseed_dict[entry['qbittorrent_save_path_with_name']])

    def _update_entry_trackers(self, torrent_hash: str) -> None:
        trackers = list(filter(lambda tracker: tracker.get('status') != 0, self.get_torrent_trackers(torrent_hash)))
        for tracker in trackers:
            self._entry_dict[torrent_hash]['qbittorrent_tracker_msg'] = tracker['msg']
            if tracker['msg']:
                break
        self._entry_dict[torrent_hash]['qbittorrent_trackers'] = trackers

    def _update_addition(self, entry: Entry) -> None:
        torrent_hash = entry['torrent_info_hash']
        torrent_properties = self.get_torrent_generic_properties(torrent_hash)
        entry['qbittorrent_seeding_time'] = torrent_properties['seeding_time']
        entry['qbittorrent_share_ratio'] = torrent_properties['share_ratio']

    def _update_reseed_addition(self, reseed_entry_list):
        reseed_last_activity = max(reseed_entry_list,
                                   key=lambda _reseed_entry: _reseed_entry['qbittorrent_last_activity'])
        for reseed_entry in reseed_entry_list:
            if reseed_entry['qbittorrent_last_activity'] <= reseed_last_activity['qbittorrent_last_activity']:
                reseed_entry['qbittorrent_reseed_last_activity'] = reseed_last_activity['qbittorrent_last_activity']

    def _update_entry_last_activity(self, entry: Entry) -> None:
        empty_time = datetime.fromtimestamp(0)
        if is_reseed_failed := entry['qbittorrent_state'] == 'pausedDL' and entry['qbittorrent_completed'] == 0:
            entry['qbittorrent_last_activity'] = empty_time
        elif is_never_activated := entry['qbittorrent_last_activity'] == empty_time or (
                entry['qbittorrent_uploaded'] == 0 and entry['qbittorrent_downloaded'] == 0):
            if entry['qbittorrent_completion_on'] > empty_time:
                entry['qbittorrent_last_activity'] = entry['qbittorrent_completion_on']
            else:
                entry['qbittorrent_last_activity'] = entry['qbittorrent_added_on']

    def _remove_torrent(self, torrent_hash: str) -> None:
        if not (torrent := self._entry_dict.get(torrent_hash)):
            self.reset_rid(reason='_remove_torrent torrent not in entry_dict')
        save_path_with_name = torrent.get('qbittorrent_save_path_with_name')
        if (torrent_list := self._reseed_dict.get(save_path_with_name)) and (torrent_hash in self._entry_dict.keys()):
            torrent_list_removed = list(
                filter(lambda t: t['torrent_info_hash'] != torrent_hash, torrent_list))
            if len(torrent_list_removed) == 0:
                del self._reseed_dict[save_path_with_name]
            else:
                self._reseed_dict[save_path_with_name] = torrent_list_removed
            del self._entry_dict[torrent_hash]
        else:
            self.reset_rid(reason='_remove_torrent torrent_list is None or torrent_hash not in entry_dict')

    def _check_action(self, action_name: str, hashes: str) -> bool:
        hashes_list = hashes.split('|')
        if not self._action_history.get(action_name):
            self._action_history[action_name] = []
        if len(set(self._action_history[action_name]) & set(hashes_list)) > 0:
            self.reset_rid(f'Duplicate operation detected: {action_name} {hashes}')
            self._action_history.clear()
            return False
        self._action_history.get(action_name).extend(hashes_list)
        return True

    def save_path_suffix(self, save_path: str) -> str:
        return save_path if save_path.endswith(os.sep) else save_path + os.sep

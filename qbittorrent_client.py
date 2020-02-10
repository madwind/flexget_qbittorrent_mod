import copy
import threading
from datetime import datetime

from flexget import plugin
from flexget.entry import Entry
from flexget.utils.tools import singleton
from loguru import logger
from requests import RequestException, Session

logger = logger.bind(name='qbittorrent_client')


@singleton
class QBittorrentClientFactory:
    _client_lock = threading.Lock()

    def __init__(self):
        self.client_map = {}

    def get_client(self, config):
        client_key = '{}{}'.format(config.get('host'), config.get('port'))
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
    API_URL_RESUME = '/api/v2/torrents/resume'
    API_URL_RECHECK_TORRENTS = '/api/v2/torrents/recheck'
    API_URL_EDIT_TRACKERS = '/api/v2/torrents/editTracker'
    API_URL_DELETE_TORRENTS = '/api/v2/torrents/delete'

    API_URL_GET_MAIN_DATA = '/api/v2/sync/maindata'
    API_URL_GET_APPLICATION_PREFERENCES = '/api/v2/app/preferences'
    API_URL_GET_TORRENT_LIST = '/api/v2/torrents/info'
    API_URL_GET_TORRENT_GENERIC_PROPERTIES = '/api/v2/torrents/properties'
    API_URL_GET_TORRENT_PIECES_STATES = '/api/v2/torrents/pieceHashes'
    API_URL_GET_TORRENT_TRACKERS = '/api/v2/torrents/trackers'

    build_entry_lock = threading.Lock()

    def __init__(self, config):
        self._reseed_dict = {}
        self._entry_dict = {}
        self._server_state = {}
        self._action_history = {}
        self._rid = 0
        self._task_dict = {}
        self._config = config
        self.connect()

    def _request(self, method, url, msg_on_fail=None, **kwargs):
        if not url.endswith(self.API_URL_LOGIN) and not self.connected:
            raise plugin.PluginError('Not connected.')
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 403 or (self.API_URL_LOGIN in url and response.text == 'Fails.'):
                msg = (
                    'Failure. URL: {}, data: {}, status_code: {}'.format(url, kwargs)
                    if not msg_on_fail
                    else msg_on_fail
                )
                self.connected = False
                self.connect()
            else:
                return response
        except RequestException as e:
            msg = str(e)
        raise plugin.PluginError(
            'Error when trying to send request to qbittorrent: {}'.format(msg)
        )

    def check_api_version(self, msg_on_fail):
        try:
            url = self.url + "/api/v2/app/webapiVersion"
            response = self.session.request('get', url)
            if response.status_code != 404:
                return response
            msg = 'Failure. URL: {}'.format(url) if not msg_on_fail else msg_on_fail
        except RequestException as e:
            msg = str(e)
        raise plugin.PluginError(
            'Error when trying to send request to qbittorrent: {}'.format(msg)
        )

    def connect(self):
        """
        Connect to qBittorrent Web UI. Username and password not necessary
        if 'Bypass authentication for localhost' is checked and host is
        'localhost'.
        """
        self.session = Session()
        if not self._config.get('verify_cert'):
            self._verify = True
        else:
            self._verify = self._config.get('verify_cert')

        self.url = '{}://{}:{}'.format('https' if self._config['use_ssl'] else 'http', self._config['host'],
                                       self._config['port']
                                       )
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

    def add_torrent_file(self, file_path, data):
        multipart_data = {k: (None, v) for k, v in data.items()}
        with open(file_path, 'rb') as f:
            multipart_data['torrents'] = f
            self._request(
                'post',
                self.url + self.API_URL_ADD_NEW_TORRENT,
                msg_on_fail='add_torrent_file failed.'.format(file_path),
                files=multipart_data,
                verify=self._verify,
            )

    def add_torrent_url(self, url, data):
        data['urls'] = url
        multipart_data = {k: (None, v) for k, v in data.items()}
        self._request(
            'post',
            self.url + self.API_URL_ADD_NEW_TORRENT,
            msg_on_fail='add_torrent_url failed.',
            files=multipart_data,
            verify=self._verify,
        )

    def delete_torrents(self, hashes, delete_files):
        data = {'hashes': hashes, 'deleteFiles': delete_files}
        if self._check_action('delete_torrents', hashes):
            self._request(
                'post',
                self.url + self.API_URL_DELETE_TORRENTS,
                data=data,
                msg_on_fail='delete_torrents failed.',
                verify=self._verify,
            )

    def recheck_torrents(self, hashes):
        data = {'hashes': hashes}
        if self._check_action('recheck_torrents', hashes):
            self._request(
                'post',
                self.url + self.API_URL_RECHECK_TORRENTS,
                data=data,
                msg_on_fail='recheck_torrents failed.',
                verify=self._verify,
            )

    def get_torrent_generic_properties(self, torrent_hash):
        data = {'hash': torrent_hash}
        return self._request(
            'post',
            self.url + self.API_URL_GET_TORRENT_GENERIC_PROPERTIES,
            data=data,
            msg_on_fail='get_torrent_generic_properties failed.',
            verify=self._verify,
        ).json()

    def get_torrent_pieces_hashes(self, torrent_hash):
        data = {'hash': torrent_hash}
        return self._request(
            'post',
            self.url + self.API_URL_GET_TORRENT_PIECES_STATES,
            data=data,
            msg_on_fail='get_torrent_pieces_hashes failed.',
            verify=self._verify,
        ).text

    def get_torrent_trackers(self, torrent_hash):
        data = {'hash': torrent_hash}
        response = self._request(
            'post',
            self.url + self.API_URL_GET_TORRENT_TRACKERS,
            data=data,
            msg_on_fail='get_torrent_trackers failed.',
            verify=self._verify
        )
        return response.json()

    def resume_torrents(self, hashes):
        data = {'hashes': hashes}
        if self._check_action('resume_torrents', hashes):
            self._request(
                'post',
                self.url + self.API_URL_RESUME,
                data=data,
                msg_on_fail='resume_torrents failed.',
                verify=self._verify,
            )

    def edit_trackers(self, torrent_hash, origurl, newurl):
        data = {'hash': torrent_hash, 'origUrl': origurl, 'newUrl': newurl}
        if self._check_action('edit_trackers', torrent_hash):
            response = self._request(
                'post',
                self.url + self.API_URL_EDIT_TRACKERS,
                data=data,
                msg_on_fail='edit_trackers failed.',
                verify=self._verify,
            )
            if response.status_code == 200:
                self._update_entry_trackers(torrent_hash)

    def add_torrent_tags(self, hashes, tags):
        data = {'hashes': hashes, 'tags': tags}
        if self._check_action('add_torrent_tags', hashes):
            self._request(
                'post',
                self.url + self.API_URL_ADD_TORRENT_TAGS,
                data=data,
                msg_on_fail='add_torrent_tags failed.',
                verify=self._verify,
            )

    def get_main_data(self):
        if self._rid == 500:
            self._rid = 0
        data = {'rid': self._rid}
        return self._request(
            'post',
            self.url + self.API_URL_GET_MAIN_DATA,
            data=data,
            msg_on_fail='get_main_data failed.',
            verify=self._verify,
        ).json()

    def get_application_preferences(self):
        return self._request(
            'post',
            self.url + self.API_URL_GET_APPLICATION_PREFERENCES,
            msg_on_fail='get_application_preferences failed.',
            verify=self._verify,
        ).json()

    def set_application_preferences(self, data):
        data = {'json': data}
        self._request(
            'get',
            self.url + self.API_URL_SET_APPLICATION_PREFERENCES,
            params=data,
            msg_on_fail='get_application_preferences failed.',
            verify=self._verify,
        )

    def get_task_data(self, task_id):
        if not self._task_dict.get(task_id):
            with self.build_entry_lock:
                if not self._task_dict.get(task_id):
                    self._build_entry()
                    self._task_dict[task_id] = {'server_state': copy.deepcopy(self._server_state),
                                                'entry_dict': copy.deepcopy(self._entry_dict),
                                                'reseed_dict': copy.deepcopy(self._reseed_dict)}
        return self._task_dict.get(task_id)

    def del_task_data(self, task_id):
        if self._task_dict.get(task_id):
            del self._task_dict[task_id]

    def _build_entry(self):
        self._building = True
        main_data = self.get_main_data()
        self._rid = main_data.get('rid')
        if main_data.get('full_update'):
            self._entry_dict = {}
            self._reseed_dict = {}

        server_state = main_data.get('server_state')
        if server_state:
            for state, value in server_state.items():
                self._server_state[state] = value

        torrents = main_data.get('torrents')
        if torrents:
            for torrent_hash, torrent in torrents.items():
                self._update_entry(torrent_hash, torrent)
        torrent_removed = main_data.get('torrents_removed')
        if torrent_removed:
            for torrent_hash in torrent_removed:
                self._remove_entry(torrent_hash)

    def _update_entry(self, torrent_hash, torrent):
        entry = self._entry_dict.get(torrent_hash)
        if not entry:
            save_path = torrent.get('save_path')
            name = torrent.get('name')
            save_path_with_name = '{}{}'.format(save_path, name)
            torrent['save_path_with_name'] = save_path_with_name
            torrent_properties = self.get_torrent_generic_properties(torrent_hash)
            torrent['seeding_time'] = torrent_properties['seeding_time']
            torrent['share_ratio'] = torrent_properties['share_ratio']
            entry = Entry(
                title=name,
                url='',
                torrent_info_hash=torrent_hash,
                content_size=torrent['size'] / (1024 * 1024 * 1024),
            )
            self._entry_dict[torrent_hash] = entry
            self._update_entry_trackers(torrent_hash)
            if not self._reseed_dict.get(save_path_with_name):
                self._reseed_dict[save_path_with_name] = []
            self._reseed_dict[save_path_with_name].append(entry)
        for key, value in torrent.items():
            if key in ['added_on', 'completion_on', 'last_activity', 'seen_complete']:
                entry['qbittorrent_' + key] = datetime.fromtimestamp(value if value > 0 else 0)
            else:
                entry['qbittorrent_' + key] = value

    def _update_entry_trackers(self, torrent_hash):
        trackers = list(filter(lambda tracker: tracker.get('status') != 0, self.get_torrent_trackers(torrent_hash)))
        self._entry_dict[torrent_hash]['qbittorrent_trackers'] = trackers

    def _remove_entry(self, torrent_hash):
        save_path_with_name = self._entry_dict.get(torrent_hash).get('qbittorrent_save_path_with_name')
        torrent_list = self._reseed_dict.get(save_path_with_name)
        if torrent_list and (torrent_hash in self._entry_dict.keys()):
            torrent_list_removed = list(
                filter(lambda torrent: torrent['torrent_info_hash'] != torrent_hash, torrent_list))
            if len(torrent_list_removed) == 0:
                del self._reseed_dict[save_path_with_name]
            else:
                self._reseed_dict[save_path_with_name] = torrent_list_removed
            del self._entry_dict[torrent_hash]
        else:
            self._rid = 0
            self._action_history.clear()
            logger.warning('Sync error, rebuild data')

    def _check_action(self, action_name, hashes):
        hashes_list = hashes.split('|')
        if not self._action_history.get(action_name):
            self._action_history[action_name] = []
        if len(set(self._action_history[action_name]) & set(hashes_list)) > 0:
            self._rid = 0
            self._action_history.clear()
            logger.warning('Duplicate operation detected: {} {}, rebuild data.', action_name, hashes)
            return False
        else:
            self._action_history.get(action_name).extend(hashes_list)
        return True

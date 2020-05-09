import copy
import threading
from datetime import datetime, timedelta
from json import JSONDecodeError

from flexget import plugin
from flexget.entry import Entry
from loguru import logger
from requests import RequestException, Session

logger = logger.bind(name='qbittorrent_client')
__version__ = 'v0.4.6'


def singleton(cls):
    instances = {}

    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return getinstance


@singleton
class QBittorrentClientFactory:
    _client_lock = threading.Lock()

    def __init__(self):
        self.client_map = {}
        logger.info('flexget_qbittorrent_mod {}', __version__)

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
        self._torrent_attr_len = 0
        self._task_dict = {}
        self._config = config
        self.connect()

    def _request(self, method, url, msg_on_fail=None, **kwargs):
        if not url.endswith(self.API_URL_LOGIN) and not self.connected:
            self.connected = False
            self._reset_rid()
            self.connect()
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 403 or (self.API_URL_LOGIN in url and response.text == 'Fails.'):
                msg = (
                    'Failure. URL: {}, data: {}, status_code: {}'.format(url, kwargs, response.status_code)
                    if not msg_on_fail
                    else msg_on_fail
                )
                self.connected = False
                self._reset_rid()
            else:
                return response
        except RequestException as e:
            self._reset_rid()
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
            response = self._request(
                'post',
                self.url + self.API_URL_ADD_NEW_TORRENT,
                msg_on_fail='add_torrent_file failed.'.format(file_path),
                files=multipart_data,
                verify=self._verify,
            )
        logger.debug('add_torrent_file response: {}', response.content)

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
        data = {'rid': self._rid}
        try:
            main_data = self._request(
                'post',
                self.url + self.API_URL_GET_MAIN_DATA,
                data=data,
                msg_on_fail='get_main_data failed.',
                verify=self._verify,
            ).json()
            return main_data
        except JSONDecodeError as e:
            msg = str(e)
            self._reset_rid()
        raise plugin.PluginError(
            'get_main_data failed.{}'.format(msg)
        )

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
                    self._task_dict.clear()
                    self._task_dict[task_id] = {'server_state': copy.deepcopy(self._server_state),
                                                'entry_dict': copy.deepcopy(self._entry_dict),
                                                'reseed_dict': copy.deepcopy(self._reseed_dict)}
        return self._task_dict.get(task_id)

    def _reset_rid(self):
        self._rid = 0

    def _build_entry(self):
        self._building = True
        main_data = self.get_main_data()
        self._rid = main_data.get('rid')
        is_new_data = main_data.get('full_update')
        if is_new_data:
            self._entry_dict = {}
            self._reseed_dict = {}
            self._action_history = {}
            self._last_update_time = datetime.now()

        server_state = main_data.get('server_state')
        if server_state:
            for state, value in server_state.items():
                self._server_state[state] = value

        torrents = main_data.get('torrents')
        if torrents:
            values = list(torrents.values())
            values_len = len(values)
            if is_new_data and values_len > 0:
                self._torrent_attr_len = len(values[0])
                logger.info('build_entry: building {} entries', values_len)
            for torrent_hash, torrent in torrents.items():
                self._update_entry(torrent_hash, torrent)
        torrent_removed = main_data.get('torrents_removed')
        if torrent_removed:
            for torrent_hash in torrent_removed:
                self._remove_torrent(torrent_hash)

        for save_path_with_name, reseed_entry_list in self._reseed_dict.items():
            self._update_reseed_addition(reseed_entry_list)

        update_addition_flag = self._last_update_time < datetime.now() - timedelta(hours=1)
        if update_addition_flag:
            self._last_update_time = datetime.now()
            for torrent_hash, entry in self._entry_dict.items():
                self._update_addition(entry)

        if is_new_data:
            logger.info('build_entry: build completion')

    def _update_entry(self, torrent_hash, torrent):
        entry = self._entry_dict.get(torrent_hash)
        is_new_entry = False
        if not entry:
            is_new_entry = True
            if len(torrent) != self._torrent_attr_len:
                self._reset_rid()
                logger.warning('Sync error: torrent lose attr, rebuild data.')
                return
            save_path = torrent['save_path']
            name = torrent['name']
            save_path_with_name = '{}{}'.format(save_path, name)
            torrent['save_path_with_name'] = save_path_with_name
            entry = Entry(
                title=name,
                url='',
                torrent_info_hash=torrent_hash,
                content_size=torrent['size'],
            )
            self._update_addition(entry)
            self._entry_dict[torrent_hash] = entry
            if not self._reseed_dict.get(save_path_with_name):
                self._reseed_dict[save_path_with_name] = []
            self._reseed_dict[save_path_with_name].append(entry)
        for key, value in torrent.items():
            if not is_new_entry and key in ['save_path', 'name']:
                self._reset_rid()
            if key in ['added_on', 'completion_on', 'last_activity', 'seen_complete']:
                timestamp = value if value > 0 else 0
                entry['qbittorrent_' + key] = datetime.fromtimestamp(timestamp)
            else:
                entry['qbittorrent_' + key] = value
                if key in ['tracker']:
                    self._update_entry_trackers(torrent_hash)
        self._update_entry_last_activity(entry)

    def _update_entry_trackers(self, torrent_hash):
        trackers = list(filter(lambda tracker: tracker.get('status') != 0, self.get_torrent_trackers(torrent_hash)))
        self._entry_dict[torrent_hash]['qbittorrent_trackers'] = trackers

    def _update_addition(self, entry):
        torrent_hash = entry['torrent_info_hash']
        torrent_properties = self.get_torrent_generic_properties(torrent_hash)
        entry['qbittorrent_seeding_time'] = torrent_properties['seeding_time']
        entry['qbittorrent_share_ratio'] = torrent_properties['share_ratio']

    def _update_reseed_addition(self, reseed_entry_list):
        reseed_last_activity = max(reseed_entry_list,
                                   key=lambda reseed_entry: reseed_entry['qbittorrent_last_activity'])
        for reseed_entry in reseed_entry_list:
            if reseed_entry['qbittorrent_last_activity'] <= reseed_last_activity['qbittorrent_last_activity']:
                reseed_entry['qbittorrent_reseed_last_activity'] = reseed_last_activity['qbittorrent_last_activity']

    def _update_entry_last_activity(self, entry):
        empty_time = datetime.fromtimestamp(0)
        is_reseed_failed = entry['qbittorrent_state'] == 'pausedDL' and entry['qbittorrent_completed'] == 0
        is_never_activated = entry['qbittorrent_last_activity'] == empty_time or (
                entry['qbittorrent_uploaded'] == 0 and entry['qbittorrent_downloaded'] == 0)
        if is_reseed_failed:
            entry['qbittorrent_last_activity'] = empty_time
        elif is_never_activated:
            if entry['qbittorrent_completion_on'] > empty_time:
                entry['qbittorrent_last_activity'] = entry['qbittorrent_completion_on']
            else:
                entry['qbittorrent_last_activity'] = entry['qbittorrent_added_on']

    def _remove_torrent(self, torrent_hash):
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
            self._reset_rid()
            logger.warning('Sync error, rebuild data')

    def _check_action(self, action_name, hashes):
        hashes_list = hashes.split('|')
        if not self._action_history.get(action_name):
            self._action_history[action_name] = []
        if len(set(self._action_history[action_name]) & set(hashes_list)) > 0:
            self._reset_rid()
            logger.warning('Duplicate operation detected: {} {}, rebuild data.', action_name, hashes)
            return False
        else:
            self._action_history.get(action_name).extend(hashes_list)
        return True

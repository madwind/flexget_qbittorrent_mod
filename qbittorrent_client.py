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
    API_URL_RESUME = '/api/v2/torrents/resume'
    API_URL_GET_TORRENT_LIST = '/api/v2/torrents/info'
    API_URL_GET_TORRENT_PIECES_STATES = '/api/v2/torrents/pieceHashes'
    API_URL_DELETE_TORRENTS = '/api/v2/torrents/delete'
    API_URL_GET_MAIN_DATA = '/api/v2/sync/maindata'
    API_URL_EDIT_TRACKERS = '/api/v2/torrents/editTracker'
    API_URL_ADD_TORRENT_TAGS = '/api/v2/torrents/addTags'
    API_URL_GET_TORRENT_TRACKERS = '/api/v2/torrents/trackers'

    build_entry_lock = threading.Lock()

    def __init__(self, config):
        self._reseed_dict = {}
        self._entry_dict = {}
        self._server_state = {}
        self._action_history = {}
        self._rid = 0
        self.connect(config)
        self._task_dict = {}

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

    def connect(self, config):
        """
        Connect to qBittorrent Web UI. Username and password not necessary
        if 'Bypass authentication for localhost' is checked and host is
        'localhost'.
        """
        self.session = Session()
        if not config.get('verify_cert'):
            self.verify = True
        else:
            self.verify = config.get('verify_cert')

        self.url = '{}://{}:{}'.format('https' if config['use_ssl'] else 'http', config['host'], config['port']
                                       )
        self.check_api_version('Check API version failed.')
        if config.get('username') and config.get('password'):
            data = {'username': config['username'], 'password': config['password']}
            response = self._request(
                'post',
                self.url + self.API_URL_LOGIN,
                data=data,
                msg_on_fail='Authentication failed.',
                verify=self.verify,
            )
            logger.debug('Successfully connected to qbittorrent')
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
                verify=self.verify,
            )

    def add_torrent_url(self, url, data):
        data['urls'] = url
        multipart_data = {k: (None, v) for k, v in data.items()}
        self._request(
            'post',
            self.url + self.API_URL_ADD_NEW_TORRENT,
            msg_on_fail='add_torrent_url failed.',
            files=multipart_data,
            verify=self.verify,
        )

    def delete_torrents(self, hashes, delete_files):
        data = {'hashes': hashes, 'deleteFiles': delete_files}
        self._request(
            'post',
            self.url + self.API_URL_DELETE_TORRENTS,
            data=data,
            msg_on_fail='delete_torrents failed.',
            verify=self.verify,
        )
        self._record_action('delete_torrents', hashes)

    def get_torrent_pieces_hashes(self, torrent_hash):
        data = {'hash': torrent_hash}
        return self._request(
            'post',
            self.url + self.API_URL_GET_TORRENT_PIECES_STATES,
            data=data,
            msg_on_fail='get_torrent_pieces_hashes failed.',
            verify=self.verify,
        ).text

    def get_torrent_trackers(self, torrent_hash):
        data = {'hash': torrent_hash}
        response = self._request(
            'post',
            self.url + self.API_URL_GET_TORRENT_TRACKERS,
            data=data,
            msg_on_fail='get_torrent_trackers failed.',
            verify=self.verify
        )
        return response.json()

    def resume_torrents(self, hashes):
        data = {'hashes': hashes}
        self._request(
            'post',
            self.url + self.API_URL_RESUME,
            data=data,
            msg_on_fail='resume_torrents failed.',
            verify=self.verify,
        )
        self._record_action('resume_torrents', hashes)

    def edit_trackers(self, torrent_hash, origurl, newurl):
        data = {'hash': torrent_hash, 'origUrl': origurl, 'newUrl': newurl}
        self._request(
            'post',
            self.url + self.API_URL_EDIT_TRACKERS,
            data=data,
            msg_on_fail='edit_trackers failed.',
            verify=self.verify,
        )
        self._record_action('edit_trackers', torrent_hash)

    def add_torrent_tags(self, hashes, tags):
        data = {'hashes': hashes, 'tags': tags}
        self._request(
            'post',
            self.url + self.API_URL_ADD_TORRENT_TAGS,
            data=data,
            msg_on_fail='add_torrent_tags failed.',
            verify=self.verify,
        )
        self._record_action('add_torrent_tags', hashes)

    def get_main_data(self):
        data = {'rid': self._rid}
        return self._request(
            'post',
            self.url + self.API_URL_GET_MAIN_DATA,
            data=data,
            msg_on_fail='get_main_data failed.',
            verify=self.verify,
        ).json()

    def get_task_data(self, task_id):
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
        with self.build_entry_lock:
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
            name = torrent.get('name')
            pieces_hashes = self.get_torrent_pieces_hashes(torrent_hash)
            name_with_pieces_hashes = '{}:{}'.format(name, pieces_hashes)
            trackers = list(filter(lambda tracker: tracker.get('status') != 0, self.get_torrent_trackers(torrent_hash)))
            entry = Entry(
                title=name,
                url='',
                torrent_info_hash=torrent_hash,
                content_size=torrent['size'] / (1024 * 1024 * 1024),
                qbittorrent_name_with_pieces_hashes=name_with_pieces_hashes,
                qbittorrent_trackers=trackers
            )
            self._entry_dict[torrent_hash] = entry
            if not self._reseed_dict.get(name_with_pieces_hashes):
                self._reseed_dict[name_with_pieces_hashes] = []
            self._reseed_dict[name_with_pieces_hashes].append(entry)
        for key, value in torrent.items():
            if key in ['added_on', 'completion_on', 'last_activity', 'seen_complete']:
                entry['qbittorrent_' + key] = datetime.fromtimestamp(value)
            else:
                entry['qbittorrent_' + key] = value

    def _remove_entry(self, torrent_hash):
        name_with_pieces_hashes = self._entry_dict.get(torrent_hash).get('qbittorrent_name_with_pieces_hashes')
        torrent_list = self._reseed_dict.get(name_with_pieces_hashes)
        if torrent_list and (torrent_hash in self._entry_dict.keys()):
            torrent_list_removed = list(
                filter(lambda torrent: torrent['torrent_info_hash'] != torrent_hash, torrent_list))
            if len(torrent_list_removed) == 0:
                del self._reseed_dict[name_with_pieces_hashes]
            else:
                self._reseed_dict[name_with_pieces_hashes] = torrent_list_removed
            del self._entry_dict[torrent_hash]
        else:
            self._rid = 0
            self._action_history.clear()
            logger.warning('Sync error, rebuild data')

    def _record_action(self, action_name, hashes):
        hashes_list = hashes.split('|')
        if not self._action_history.get(action_name):
            self._action_history[action_name] = []
        if len(set(self._action_history[action_name]) & set(hashes_list)) > 0:
            self._rid = 0
            self._action_history.clear()
            logger.warning('Two identical operations were performed on the same seed, rebuild data.')
        else:
            self._action_history.get(action_name).extend(hashes_list)

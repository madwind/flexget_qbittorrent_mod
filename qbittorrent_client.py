from flexget import plugin
from loguru import logger
from requests import RequestException, Session

logger = logger.bind(name='qbittorrent_client')


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

    def __init__(self, config):
        self.connect(config)

    def _request(self, method, url, msg_on_fail=None, **kwargs):
        if not url.endswith(self.API_URL_LOGIN) and not self.connected:
            raise plugin.PluginError('Not connected.')
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 403:
                msg = (
                    'Failure. URL: {}, data: {}'.format(url, kwargs)
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
            self._request(
                'post',
                self.url + self.API_URL_LOGIN,
                data=data,
                msg_on_fail='Authentication failed.',
                verify=self.verify,
            )
        logger.debug('Successfully connected to qbittorrent')
        self.connected = True

    @property
    def torrents(self):
        return list(self._request(
            'post',
            self.url + self.API_URL_GET_TORRENT_LIST,
            msg_on_fail='get_torrents failed.',
            verify=self.verify,
        ).json())

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
        return self._request(
            'post',
            self.url + self.API_URL_GET_TORRENT_TRACKERS,
            data=data,
            msg_on_fail='get_torrent_trackers failed.',
            verify=self.verify,
        ).json()

    def resume_torrents(self, hashes):
        data = {'hashes': hashes}
        self._request(
            'post',
            self.url + self.API_URL_RESUME,
            data=data,
            msg_on_fail='resume_torrents failed.',
            verify=self.verify,
        )

    def edit_trackers(self, torrent_hash, origurl, newurl):
        data = {'hash': torrent_hash, 'origUrl': origurl, 'newUrl': newurl}
        self._request(
            'post',
            self.url + self.API_URL_EDIT_TRACKERS,
            data=data,
            msg_on_fail='edit_trackers failed.',
            verify=self.verify,
        )

    def add_torrent_tags(self, hashes, tags):
        data = {'hashes': hashes, 'tags': tags}
        self._request(
            'post',
            self.url + self.API_URL_ADD_TORRENT_TAGS,
            data=data,
            msg_on_fail='add_torrent_tags failed.',
            verify=self.verify,
        )

    @property
    def main_data(self):
        return self._request(
            'post',
            self.url + self.API_URL_GET_MAIN_DATA,
            msg_on_fail='get_main_data failed.',
            verify=self.verify,
        ).json()

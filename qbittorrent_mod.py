import os
from datetime import datetime

from flexget.entry import Entry
from loguru import logger
from requests import Session
from requests.exceptions import RequestException

from flexget import plugin
from flexget.event import event

logger = logger.bind(name='qbittorrent_mod')


class QBittorrentClient:
    API_URL_LOGIN = '/api/v2/auth/login'
    API_URL_UPLOAD = '/api/v2/torrents/add'
    API_URL_DOWNLOAD = '/api/v2/torrents/add'
    API_URL_RESUME = '/api/v2/torrents/resume'
    API_GET_TORRENT_LIST = '/api/v2/torrents/info'
    API_GET_TORRENT_PIECES_STATES = '/api/v2/torrents/pieceStates'
    API_DELETE_TORRENTS = '/api/v2/torrents/delete'

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
        self.verify = config['verify_cert']

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

    def get_session(self):
        return self.session

    def get_torrents(self):
        return list(self._request(
            'post',
            self.url + self.API_GET_TORRENT_LIST,
            msg_on_fail='get_torrents failed.',
            verify=self.verify,
        ).json())

    def add_torrent_file(self, file_path, data):
        multipart_data = {k: (None, v) for k, v in data.items()}
        with open(file_path, 'rb') as f:
            multipart_data['torrents'] = f
            self._request(
                'post',
                self.url + self.API_URL_UPLOAD,
                msg_on_fail='add_torrent_file failed.'.format(file_path),
                files=multipart_data,
                verify=self.verify,
            )

    def add_torrent_url(self, url, data):
        data['urls'] = url
        multipart_data = {k: (None, v) for k, v in data.items()}
        self._request(
            'post',
            self.url + self.API_URL_DOWNLOAD,
            msg_on_fail='add_torrent_url failed.',
            files=multipart_data,
            verify=self.verify,
        )

    def delete_torrents(self, hashes, delete_files):
        data = {'hashes': hashes, 'deleteFiles': delete_files}
        self._request(
            'post',
            self.url + self.API_DELETE_TORRENTS,
            data=data,
            msg_on_fail='Authentication failed.',
            verify=self.verify,
        )

    def get_torrent_pieces_hashes(self, torrent_hash):
        data = {'hash': torrent_hash}
        self._request(
            'post',
            self.url + self.API_DELETE_TORRENTS,
            data=data,
            msg_on_fail='get_torrent_pieces_hashes failed.',
            verify=self.verify,
        )

    def resume_torrents(self, hashes):
        data = {'hashes': hashes}
        self._request(
            'post',
            self.url + self.API_URL_RESUME,
            data=data,
            msg_on_fail='resume_torrents failed.',
            verify=self.verify,
        )


class QBittorrentModBase:
    def __init__(self):
        self.client = None

    def prepare_config(self, config):
        if isinstance(config, bool):
            config = {'enabled': config}
        config.setdefault('enabled', True)
        config.setdefault('host', 'localhost')
        config.setdefault('port', 8080)
        config.setdefault('use_ssl', True)
        config.setdefault('verify_cert', True)
        return config

    def create_client(self, config):
        cli = QBittorrentClient(config)
        return cli

    def on_task_start(self, task, config):
        self.client = None
        config = self.prepare_config(config)
        if config['enabled']:
            if task.options.test:
                logger.info('Trying to connect to qBittorrent...')
                self.client = self.create_client(config)
                if self.client:
                    logger.info('Successfully connected to qBittorrent.')
                else:
                    logger.error('It looks like there was a problem connecting to qBittorrent.')


class PluginQBittorrentModInput(QBittorrentModBase):
    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'host': {'type': 'string'},
                    'use_ssl': {'type': 'boolean'},
                    'port': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'password': {'type': 'string'},
                    'verify_cert': {'type': 'boolean'},
                    'enabled': {'type': 'boolean'},
                    'only_complete': {'type': 'boolean'},
                },
                'additionalProperties': False
            }
        ]
    }

    def prepare_config(self, config):
        config = QBittorrentModBase.prepare_config(self, config)
        config.setdefault('only_complete', False)
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)

        if not config['enabled']:
            return
        if not self.client:
            self.client = self.create_client(config)
        entries = []

        for torrent in self.client.get_torrents():
            entry = Entry(
                title=torrent['name'],
                url='',
                torrent_info_hash=torrent['hash'],
                content_size=torrent['size'] / (1024 * 1024),
            )
            for key, value in torrent.items():
                if key in ['added_on', 'completion_on', 'last_activity', 'seen_complete']:
                    entry['qbittorrent_' + key] = datetime.fromtimestamp(value)
                else:
                    entry['qbittorrent_' + key] = value
            entries.append(entry)
        return entries


class PluginQBittorrentMod(QBittorrentModBase):
    """
    Example:

      qbittorrent__mod:
        username: <USERNAME> (default: (none))
        password: <PASSWORD> (default: (none))
        host: <HOSTNAME> (default: localhost)
        port: <PORT> (default: 8080)
        use_ssl: <SSL> (default: False)
        verify_cert: <VERIFY> (default: True)
        path: <OUTPUT_DIR> (default: (none))
        category: <CATEGORY> (default: (none))
        maxupspeed: <torrent upload speed limit> (default: 0)
        maxdownspeed: <torrent download speed limit> (default: 0)
        add_paused: <ADD_PAUSED> (default: False)
    """

    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'host': {'type': 'string'},
                    'use_ssl': {'type': 'boolean'},
                    'port': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'password': {'type': 'string'},
                    'verify_cert': {'type': 'boolean'},
                    'action': {
                        'type': 'object',
                        'properties': {
                            'add': {
                                'type': 'object',
                                'properties': {
                                    'savepath': {'type': 'string'},
                                    'cookie': {'type': 'string'},
                                    'category': {'type': 'string'},
                                    'skip_checking': {'type': 'string'},
                                    'paused': {'type': 'string'},
                                    'root_folder': {'type': 'string'},
                                    'rename': {'type': 'string'},
                                    'upLimit': {'type': 'integer'},
                                    'dlLimit': {'type': 'integer'},
                                    'autoTMM': {'type': 'boolean'},
                                    'sequentialDownload': {'type': 'string'},
                                    'firstLastPiecePrio': {'type': 'string'}
                                }
                            },
                            'remove': {
                                'type': 'object',
                                'properties': {
                                    'delete_files': {'type': 'boolean'}
                                }
                            },
                            'resume': {
                                'type': 'object',
                                'properties': {
                                    'only_complete': {'type': 'boolean'}
                                }
                            }
                        }
                    },
                    'fail_html': {'type': 'boolean'}
                },
                'additionalProperties': False,
            }
        ]
    }

    def prepare_config(self, config):
        config = QBittorrentModBase.prepare_config(self, config)
        config.setdefault('fail_html', True)
        config.setdefault('action', {})
        return config

    @plugin.priority(120)
    def on_task_download(self, task, config):
        """
        Call download plugin to generate torrent files to load into
        qBittorrent.
        """
        config = self.prepare_config(config)
        if not config['enabled']:
            return
        # If the download plugin is not enabled, we need to call it to get our temp .torrent files

        if 'download' not in task.config:
            download = plugin.get('download', self)
            for entry in task.accepted:
                if entry.get('transmission_id'):
                    # The torrent is already loaded in deluge, we don't need to get anything
                    continue
                if list(config['action'])[0] != 'add' and entry.get('torrent_info_hash'):
                    # If we aren't adding the torrent new, all we need is info hash
                    continue
                download.get_temp_file(task, entry, handle_magnets=True, fail_html=config['fail_html'])

    @plugin.priority(135)
    def on_task_output(self, task, config):
        config = self.prepare_config(config)
        if len(config['action']) != 1:
            raise plugin.PluginError('There must be and only one action')
        # don't add when learning
        if task.options.learn:
            return
        if not config['enabled']:
            return
            # Do not run if there is nothing to do
        if not task.accepted:
            return
        if self.client is None:
            self.client = self.create_client(config)
            if self.client:
                logger.debug('Successfully connected to qBittorrent.')
            else:
                raise plugin.PluginError("Couldn't connect to qBittorrent.")

        if config['action'].get('add'):
            for entry in task.accepted:
                self.add_entries(task, entry, config)
                logger.info('qBittorrent: add {}', entry['title'])
        elif config['action'].get('remove'):
            session_torrents = self.client.get_torrents()
            self.remove_entries(task, session_torrents, config)
        elif config['action'].get('resume'):
            self.resume_entries(task, config)
        else:
            raise plugin.PluginError('Not connected.')

    def add_entries(self, task, entry, config):
        add_options = config['action']['add']
        if add_options.get('autoTMM') and add_options.get('savepath'):
            del add_options['savepath']

        is_magnet = entry['url'].startswith('magnet:')

        if task.manager.options.test:
            logger.info('Test mode.')
            logger.info('Would add torrent to qBittorrent with:')
            if not is_magnet:
                logger.info('File: {}', entry.get('file'))
            else:
                logger.info('Url: {}', entry.get('url'))
            logger.info('Save path: {}', add_options.get('savepath'))
            logger.info('Category: {}', add_options.get('category'))
            logger.info('Paused: {}', add_options.get('paused', 'false'))
            if add_options.get('upLimit'):
                logger.info('Upload Speed Limit: {}', add_options.get('upLimit'))
            if add_options.get('dlLimit'):
                logger.info('Download Speed Limit: {}', add_options.get('dlLimit'))
            return

        if not is_magnet:
            if 'file' not in entry:
                entry.fail('File missing?')
                return
            if not os.path.exists(entry['file']):
                tmp_path = os.path.join(task.manager.config_base, 'temp')
                logger.debug('entry: {}', entry)
                logger.debug('temp: {}', ', '.join(os.listdir(tmp_path)))
                entry.fail("Downloaded temp file '%s' doesn't exist!?" % entry['file'])
                return
            self.client.add_torrent_file(entry['file'], add_options)
        else:
            self.client.add_torrent_url(entry['url'], add_options)

    def remove_entries(self, task, session_torrents, config):
        remove_options = config['action']['remove']
        delete_files = remove_options.get('delete_files')
        hashes = []
        for entry in task.accepted:
            logger.info('qBittorrent: delete {}', entry['title'])
            hashes.append(entry['torrent_info_hash'])
        self.client.delete_torrents(str.join('|', hashes), delete_files)

    def resume_entries(self, task, config):
        resume_options = config['action']['resume']
        only_complete = resume_options.get('only_complete')
        hashes = []
        for entry in task.accepted:
            hashes.append(entry['torrent_info_hash'])
            logger.info('qBittorrent: resume {}', entry['title'])
        self.client.resume_torrents(str.join('|', hashes))

    def on_task_learn(self, task, config):
        """ Make sure all temp files are cleaned up when entries are learned """
        # If download plugin is enabled, it will handle cleanup.
        if 'download' not in task.config:
            download = plugin.get('download', self)
            download.cleanup_temp_files(task)

    on_task_abort = on_task_learn


@event('plugin.register')
def register_plugin():
    plugin.register(PluginQBittorrentMod, 'qbittorrent_mod', api_ver=2)
    plugin.register(PluginQBittorrentModInput, 'from_qbittorrent_mod', api_ver=2)

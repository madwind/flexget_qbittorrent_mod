import datetime
import re
from abc import ABC, abstractmethod
from re import Match
from typing import Union, Optional
from urllib.parse import urljoin

import requests
from dateutil.parser import parse
from flexget.entry import Entry
from loguru import logger
from requests import Response
from requests.adapters import HTTPAdapter

from .base import NetworkState, Work
from .get_details import get_details_base
from ..utils import net_utils, url_recorder


class SiteBase(ABC):
    @property
    @abstractmethod
    def URL(self):
        return None

    USER_CLASSES: dict = None
    DOWNLOAD_PAGE = 'download.php?id={torrent_id}'

    def __init__(self):
        self.session = None

    @classmethod
    def build_sign_in_schema(cls):
        return {cls.get_module_name(): {'type': 'string'}}

    @classmethod
    def build_reseed_schema(cls):
        return {cls.get_module_name(): {'type': 'string'}}

    @classmethod
    def get_module_name(cls):
        return cls.__module__.rsplit('.', maxsplit=1)[-1]

    @classmethod
    def build_sign_in_entry(cls, entry: Entry, config: dict) -> None:
        entry['url'] = cls.URL
        site_config: Union[str, dict] = entry['site_config']
        headers: dict = {
            'user-agent': config.get('user-agent'),
            'referer': entry['url'],
            'accept-encoding': 'gzip, deflate, br',
        }
        cookie: Optional[str] = None
        if isinstance(site_config, str):
            cookie = site_config
        elif isinstance(site_config, dict):
            cookie = site_config.get('cookie')
        if cookie:
            entry['cookie'] = cookie
        entry['headers'] = headers
        entry['user_classes'] = cls.USER_CLASSES

    def build_login_workflow(self, entry: Entry, config: dict) -> list[Work]:
        return []

    def build_login_data(self, login: dict, last_content) -> dict:
        return {}

    def build_workflow(self, entry: Entry, config: dict) -> list[Work]:
        return []

    def build_selector(self):
        return {}

    def get_details(self, entry, config):
        get_details_base(self, entry, config, self.build_selector())

    def get_message(self, entry, config: dict) -> None:
        entry['result'] += '(TODO: Message)'

    @classmethod
    def build_reseed_entry(cls, entry: Entry, config: dict, site, passkey, torrent_id) -> None:
        cls.build_reseed_entry_from_url(entry, config, site, passkey, torrent_id)

    @classmethod
    def build_reseed_entry_from_url(cls, entry: Entry, config: dict, site, passkey, torrent_id) -> None:
        if isinstance(passkey, dict):
            user_agent: str = config.get('user-agent')
            cookie: str = passkey.get('cookie')
            entry['headers']: dict = {
                'user-agent': user_agent,
            }
            entry['cookie'] = cookie
            download_page = cls.DOWNLOAD_PAGE.format(torrent_id=torrent_id)
        else:
            download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = f"https://{site['base_url']}/{download_page}"

    @classmethod
    def build_reseed_from_page(cls, entry: Entry, config: dict, passkey, torrent_id, base_url, torrent_page_url,
                               url_regex) -> None:
        record = url_recorder.load_record(entry['class_name'])
        now = datetime.datetime.now()
        expire = datetime.timedelta(days=7)
        if torrent := record.get(torrent_id):
            if parse(torrent['expire']) > now - expire:
                entry['url'] = torrent['url']
                return
        download_url = ''
        try:
            torrent_page_url = urljoin(base_url, torrent_page_url.format(torrent_id=torrent_id))
            session = requests.Session()
            user_agent = config.get('user-agent')
            cookie = passkey.get('cookie')
            headers = {
                'user-agent': user_agent,
                'referer': base_url
            }
            session.headers.update(headers)
            session.cookies.update(net_utils.cookie_str_to_dict(cookie))
            response = session.get(torrent_page_url, timeout=60)
            if response is not None and response.status_code == 200:
                if re_search := re.search(url_regex, response.text):
                    download_url = urljoin(base_url, re_search.group())
        except Exception as e:
            logger.warning(e)
        if not download_url:
            entry.fail(f"site:{entry['class_name']} can not found download url from {torrent_page_url}")
        entry['url'] = download_url
        record[torrent_id] = {'url': download_url, 'expire': (now + expire).strftime('%Y-%m-%d')}
        url_recorder.save_record(entry['class_name'], record)

    def request(self, entry, method: str, url: str, **kwargs) -> Optional[Response]:
        if not self.session:
            self.session = requests.Session()
            if entry_headers := entry.get('headers'):
                self.session.headers.update(entry_headers)
            if entry_cookie := entry.get('cookie'):
                self.session.cookies.update(net_utils.cookie_str_to_dict(entry_cookie))
            self.session.mount('http://', HTTPAdapter(max_retries=2))
            self.session.mount('https://', HTTPAdapter(max_retries=2))
        try:
            response: Response = self.session.request(method, url, timeout=60, **kwargs)
            if response is not None and response.status_code != 200:
                entry.fail_with_prefix(f'response.status_code={response.status_code}')
            return response
        except Exception as e:
            entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=url, error=e))
        return None

    def sign_in_by_get(self, entry, config: dict, work: Work, last_content: Optional[str] = None) -> Response:
        return self.request(entry, 'get', work.url)

    def sign_in_by_post(self, entry, config: dict, work: Work,
                        last_content: Optional[str] = None) -> Optional[Response]:
        data = {}
        for key, regex in work.data.items():
            if key == 'fixed':
                net_utils.dict_merge(data, regex)
            else:
                value_search: Match = re.search(regex, last_content)
                if value_search:
                    data[key] = value_search.group()
                else:
                    entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, work.url))
                    return
        return self.request(entry, 'post', work.url, data=data)

    def sign_in_by_login(self, entry, config: dict, work: Work, last_content: str) -> Optional[Response]:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        return self.request(entry, 'post', work.url, data=self.build_login_data(login, last_content))

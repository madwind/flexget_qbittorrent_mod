from __future__ import annotations

import datetime
import re
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from dateutil.parser import parse
from flexget.entry import Entry
from loguru import logger

from ..utils import url_recorder
from ..utils.net_utils import get_module_name, cookie_str_to_dict


class Reseed(ABC):
    @classmethod
    @abstractmethod
    def reseed_build_schema(cls):
        pass

    @abstractmethod
    def reseed_build_entry(self,
                           entry: Entry,
                           config: dict,
                           site: dict,
                           passkey: str | dict,
                           torrent_id: str,
                           ) -> None:
        pass


class ReseedPasskey(Reseed, ABC):
    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {get_module_name(cls): {'type': 'string'}}

    def reseed_build_entry(self, entry: Entry, config: dict, site: dict, passkey: str, torrent_id: str) -> None:
        download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = f"https://{site['base_url']}/{download_page}"


class ReseedCookie(Reseed, ABC):
    DOWNLOAD_PAGE_TEMPLATE = 'download.php?id={torrent_id}'

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def reseed_build_entry(self, entry: Entry, config: dict, site: dict, passkey: dict, torrent_id: str) -> None:
        user_agent = config.get('user-agent')
        cookie = passkey.get('cookie')
        entry['headers'] = {
            'user-agent': user_agent
        }
        entry['cookie'] = cookie
        download_page = self.DOWNLOAD_PAGE_TEMPLATE.format(torrent_id=torrent_id)
        entry['url'] = f"https://{site['base_url']}/{download_page}"


class ReseedPage(Reseed, ABC):

    @property
    @abstractmethod
    def URL(self) -> str:
        pass

    @property
    @abstractmethod
    def TORRENT_PAGE_URL(self) -> str:
        pass

    @property
    @abstractmethod
    def DOWNLOAD_URL_REGEX(self) -> str:
        pass

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def reseed_build_entry(self, entry: Entry, config: dict, site: dict, passkey: dict, torrent_id: str) -> None:
        record = url_recorder.load_record(entry['class_name'])
        now = datetime.datetime.now()
        expire = datetime.timedelta(days=7)
        if (torrent := record.get(torrent_id)) and parse(torrent['expire']) > now - expire:
            entry['url'] = torrent['url']
            return
        download_url = ''
        torrent_page_url = urljoin(self.URL, self.TORRENT_PAGE_URL.format(torrent_id=torrent_id))
        try:
            session = requests.Session()
            user_agent = config.get('user-agent')
            cookie = passkey.get('cookie')
            headers = {
                'user-agent': user_agent,
                'referer': self.URL
            }
            session.headers.update(headers)
            session.cookies.update(cookie_str_to_dict(cookie))
            response = session.get(torrent_page_url, timeout=60)
            if response is not None and response.status_code == 200 and (
                    re_search := re.search(self.DOWNLOAD_URL_REGEX, response.text)):
                download_url = urljoin(self.URL, re_search.group())
        except Exception as e:
            logger.warning(e)
        if not download_url:
            entry.fail(f"site:{entry['class_name']} can not found download url from {torrent_page_url}")
        entry['url'] = download_url
        record[torrent_id] = {'url': download_url, 'expire': (now + expire).strftime('%Y-%m-%d')}
        url_recorder.save_record(entry['class_name'], record)

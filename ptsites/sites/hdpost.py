from __future__ import annotations

import re
from typing import Final
from urllib.parse import urljoin

from flexget.entry import Entry
from flexget.utils.soup import get_soup

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.reseed import Reseed
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.unit3d import Unit3D
from ..utils import net_utils
from ..utils.net_utils import get_module_name
from ..utils.value_handler import handle_join_date, handle_infinite


class MainClass(Unit3D, Reseed):
    URL: Final = 'https://pt.hdpost.top'
    USER_CLASSES: Final = {
        'uploaded': [109951162777600],
        'days': [365]
    }

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'},
                    'login': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string'},
                            'password': {'type': 'string'}
                        },
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            }
        }

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'rsskey': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method=self.sign_in_by_login,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                response_urls=['', '/pages/1'],
            )
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[('https://pt.hdpost.top/users/(.*?)/', 1)],
                assert_state=(check_final_state, SignState.SUCCEED),
                use_last_content=True,
                is_base_content=True,
                response_urls=['', '/pages/1'],
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        login_page = get_soup(last_content)
        hidden_input = login_page.select_one('form > input:nth-last-child(2)')
        name = hidden_input.attrs['name']
        value = hidden_input.attrs['value']
        return {
            '_token': re.search(r'(?<=name="_token" value=").+?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
            '_captcha': re.search(r'(?<=name="_captcha" value=").+?(?=")', last_content).group(),
            '_username': '',
            name: value,
        }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'user_id': '/users/(.*?)/',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': 'ul.top-nav__ratio-bar',
                        'header': '.profile__registration',
                        'data_table': 'aside'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '上传.+?([\\d.]+ [ZEPTGMK]?iB)',
                             'handle': self.remove_symbol
                },
                'downloaded': {
                    'regex': '下载.+?([\\d.]+ [ZEPTGMK]?iB)',
                    'handle': self.remove_symbol
                },
                'share_ratio': {
                    'regex': '分享率.+?([\\d.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': '魔力.+?(\\d[\\d,. ]*)',
                    'handle': self.handle_points
                },
                'join_date': {
                    'regex': r'注册日期.*?(\d{4}-\d{2}-\d{2})',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': '做种.+?(\\d+)'
                },
                'leeching': {
                    'regex': '吸血.+?(\\d+)'
                },
                'hr': {
                    'regex': 'H&amp;R.+?(\\d+)'
                }
            }
        })
        return selector

    @classmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site: dict, passkey: str | dict,
                           torrent_id: str) -> None:
        download_page = site['download_page'].format(torrent_id=torrent_id, rsskey=passkey['rsskey'])
        entry['url'] = urljoin(MainClass.URL, download_page)

    def remove_symbol(self, value: str):
        return value.replace('\xa0', '')
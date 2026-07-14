from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.net_utils import get_module_name
from ..utils.value_handler import handle_infinite, handle_join_date


class MainClass(PrivateTorrent):
    URL: Final = 'https://pussytorrents.org/'

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
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

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/user/account/login/',
                method=self.sign_in_by_login,
                succeed_regex=[r'Welcome back,</span> <b><a href="/profile/\w+">\w+'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
            'remember_me': 'on',
            'is_forum_login': ''
        }

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'Welcome back,</span> <b><a href="/profile/(.+?)">',
            'detail_sources': {
                'default': {
                    'link': '/profile/{}',
                    'elements': {
                        'bar': '#memberBar > div.span8',
                        'join date': '#profileTable > tbody > tr:nth-child(1)'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'UL: ([\d.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': r'DL: ([\d.]+ [ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': r'Ratio: (∞|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': None,
                'join_date': {
                    'regex': r'Join Date((\w+ ){3}\w+)',
                    'handle': handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

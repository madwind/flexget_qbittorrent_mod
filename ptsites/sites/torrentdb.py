import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import SignState, check_final_state
from ..base.work import Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.net_utils import get_module_name
from ..utils.value_hanlder import handle_infinite, handle_join_date


class MainClass(PrivateTorrent):
    URL: Final = 'https://torrentdb.net'
    USER_CLASSES: Final = {
        'uploaded': [10995116277760],
        'days': [1095],
        'share_ratio': [2]
    }

    @classmethod
    def sign_in_build_schema(cls):
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
                url='/login',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method=self.sign_in_by_login,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=[''],
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            '_token': re.search(r'(?<=name="_token" value=").+?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
        }

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'<strong class="align-middle">(.+?)</strong>',
            'detail_sources': {
                'default': {
                    'link': '/profile/{}',
                    'elements': {
                        'join_date': 'div.bg-gray-light.rounded.p-5 div:nth-child(4) > div:nth-child(2)',
                        'table': 'div.bg-gray-light.rounded.p-5 > div > div.mt-2.lg\:mt-0'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'≈.*?([\d.]+ [ZEPTGMK]?B) '
                },
                'downloaded': {
                    'regex': r'([\d.]+ [ZEPTGMK]?B) ≈'
                },
                'share_ratio': {
                    'regex': r'Tokens\s*(∞|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'([\d,.]+)(?= BP)'
                },
                'join_date': {
                    'regex': r'Joined on (\w+ \w+ \w+)',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': r'Total seeding: ([\d,]+)'
                },
                'leeching': {
                    'regex': r'Total leeching: ([\d,]+)'
                },
                'hr': None
            }
        }

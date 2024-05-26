from __future__ import annotations

import re
from typing import Final

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.net_utils import get_module_name
from ..utils.value_handler import handle_join_date, handle_infinite


class MainClass(PrivateTorrent):
    URL: Final = 'https://www.myanonamouse.net/'
    USER_CLASSES: Final = {
        'uploaded': [26843545600],
        'share_ratio': [2.0],
        'days': [28]
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

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login.php',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/takelogin.php',
                method=self.sign_in_by_login,
                succeed_regex=['Log Out'],
                response_urls=['/u/'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                t_regex='<input type="hidden" name="t" value="([^"]+)"',
                a_regex='<input type="hidden" name="a" value="([^"]+)"',
            )
        ]

    def sign_in_by_login(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return None
        print(last_content)
        t = re.search(work.t_regex, last_content).group(1)
        j = len(t)
        a = re.search(work.a_regex, last_content).group(1)
        data = {
            't': (None, t),
            'j': (None, j),
            'a': (None, a),
            'email': (None, login['username']),
            'password': (None, login['password']),
            'rememberMe': (None, 'yes')
        }
        response = self.request(entry, 'post', work.url, data=data)
        return response

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': '/u/(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/u/{}',
                    'elements': {
                        'bar': '.mmUserStats ul',
                        'table': 'table.coltable'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded\s+?([\d.]+ [ZEPTGMK]i?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded\s+?([\d.]+ [ZEPTGMK]i?B)'
                },
                'share_ratio': {
                    'regex': r'Share Ratio.*?(∞|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'Bonus:\s+([\d,.]+)'
                },
                'join_date': {
                    'regex': r'Join date\s*?(\d{4}-\d{2}-\d{2})',
                    'handle': handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

import hashlib
from typing import Final

from ..base.entry import SignInEntry
from ..base.request import NetworkState, check_network_state
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.net_utils import get_module_name
from ..utils.value_hanlder import handle_infinite


class MainClass(PrivateTorrent):
    URL: Final = 'https://www.gay-torrents.net/'

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
                url='/login.php?do=login',
                method=self.sign_in_by_login,
                succeed_regex=[r'Thank you for logging in, .*?\.</p>'],
                assert_state=(check_network_state, NetworkState.SUCCEED),
                response_urls=['/login.php?do=login']
            )
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/latest/',
                method=self.sign_in_by_get,
                succeed_regex=['Log Out'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/latest/']
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'do': 'login',
            'vb_login_md5password': hashlib.md5(login['password'].encode()).hexdigest(),
            'vb_login_md5password_utf': hashlib.md5(login['password'].encode()).hexdigest(),
            's': '',
            'securitytoken': 'guest',
            'url': '/latest/',
            'vb_login_username': login['username'],
            'vb_login_password': login['password'],
            'cookieuser': 1
        }

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'<a href="member\.php\?([-\w]+?)">My Profile</a>',
            'detail_sources': {
                'default': {
                    'link': '/member.php?{}',
                    'elements': {
                        'table1': '#view-stats_mini > div > div > div',
                        'table2': '#view-stats_mini.subsection > div > div > div'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded\s*([\d.]+ ([ZEPTGMK]i)?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded\s*([\d.]+ ([ZEPTGMK]i)?B)'
                },
                'share_ratio': {
                    'regex': r'Ratio(∞|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'Juices([\d,.]+)'
                },
                'join_date': {
                    'regex': r'Join Date\s*?[\d:]+? (.+?)\s',
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

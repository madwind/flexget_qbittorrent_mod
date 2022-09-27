from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.net_utils import get_module_name
from ..utils.value_handler import handle_infinite, handle_join_date


class MainClass(PrivateTorrent):
    URL: Final = 'https://www.gaytor.rent/'
    USER_CLASSES: Final = {
        'downloaded': [858993459200],
        'share_ratio': [1.05],
        'days': [28]
    }

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
                url='/takelogin.php',
                method=self.sign_in_by_login,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
            'sw': '1920:1080'
        }

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'id=(\d+)"><i class="icon-tools"></i> Details',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'bar': '#navbar li.dropdown.text-nowrap li:nth-child(8) > a',
                        'table': 'div:nth-child(2) table:nth-child(11) > tbody'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded.*?([\d.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded.*?([\d.]+ [ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': r'Share ratio.*?(∞|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'Total Seed Bonus([\d,.]+)'
                },
                'join_date': {
                    'regex': r'Join\sdate\s*?(\d{4}-\d{2}-\d{2})',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': r'\s*([\d,]+)'
                },
                'leeching': {
                    'regex': r'\s*[\d,]+\s*([\d,]+)'
                },
                'hr': None
            }
        }

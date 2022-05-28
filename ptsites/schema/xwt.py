from abc import ABC

from .private_torrent import PrivateTorrent
from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..utils.net_utils import get_module_name
from ..utils.value_hanlder import handle_infinite


class XWT(PrivateTorrent, ABC):
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
                succeed_regex=[r'Top 5 Torrents'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
            'returnto': '/'
        }

    @property
    def details_selector(self) -> dict:
        return {
            'detail_sources': {
                'default': {
                    'link': '/browse.php',
                    'elements': {
                        'ratio': '#wel-radio',
                        'up': '#wel-radiok',
                        'down': '#wel-radio2',
                        'active': '#wel-radio3'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Up:\s*([\d.]+ (?i:[ZEPTGMK])B)'
                },
                'downloaded': {
                    'regex': r'(?i)Down:\s*([\d.]+ [ZEPTGMK]B)'
                },
                'share_ratio': {
                    'regex': r'Ratio:\s*(---|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': None,
                'seeding': {
                    'regex': r'Active:\s*(\d+)'
                },
                'leeching': {
                    'regex': r'Active:\s*\d+\s*(\d+)'
                },
                'hr': None
            }
        }

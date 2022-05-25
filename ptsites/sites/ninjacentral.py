from ..base.sign_in import check_final_state, SignState, Work
from ..utils.net_utils import get_module_name
from ..schema.private_torrent import PrivateTorrent


class MainClass(PrivateTorrent):
    URL = 'https://ninjacentral.co.za/'

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

    def sign_in_build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login',
                method=self.sign_in_by_login,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_build_login_data(self, login, last_content):
        return {
            'redirect': '',
            'username': login['username'],
            'password': login['password'],
            'rememberme': 'on'
        }

    @property
    def details_selector(self) -> dict:
        return {
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'link': '/profile',
                    'elements': {
                        'table': '#content > div > div > table:nth-child(1) > tbody > tr:nth-child(3) > td',
                    }
                }
            },
            'details': {
                'uploaded': None,
                'downloaded': None,
                'share_ratio': None,
                'points': None,
                'join_date': {
                    'regex': r'''(?x)(\d {4} - \d {2} - \d {2})'''
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

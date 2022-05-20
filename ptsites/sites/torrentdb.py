import re

from ..schema.site_base import SignState, Work, NetworkState, SiteBase
from ..utils.value_hanlder import handle_infinite, handle_join_date


class MainClass(SiteBase):
    URL = 'https://torrentdb.net'
    USER_CLASSES = {
        'uploaded': [10995116277760],
        'days': [1095],
        'share_ratio': [2]
    }

    @classmethod
    def build_sign_in_schema(cls):
        return {
            cls.get_module_name(): {
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

    def build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method='login',
                succeed_regex='Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=[''],
            )
        ]

    def build_login_data(self, login, last_content):
        return {
            '_token': re.search(r'(?<=name="_token" value=").+?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
        }

    def build_selector(self):
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

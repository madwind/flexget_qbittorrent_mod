import re

from dateutil.parser import parse

from ..schema.site_base import SignState, Work, NetworkState, SiteBase


def handle_share_ratio(value):
    if value == '∞':
        return '0'
    else:
        return value


def handle_join_date(value):
    return parse(value).date()


def build_selector():
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
                'handle': handle_share_ratio
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
                method='password',
                succeed_regex='Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=[''],
                token_regex=r'(?<=name="_token" value=").+?(?=")',
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            '_token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

    def get_details(self, entry, config):
        self.get_details_base(entry, config, build_selector())

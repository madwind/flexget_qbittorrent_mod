import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_share_ratio(value):
    if value == '∞':
        return '0'
    else:
        return value


def handle_join_date(value):
    value_split = value.replace(',', '').split()
    return datetime.now() - relativedelta(
        **dict((unit if unit.endswith('s') else f'{unit}s', int(amount)) for amount, unit in
               [value_split[i:i + 2] for i in range(0, len(value_split), 2)]))


def build_selector():
    return {
        'user_id': r'(?<="/user\.php\?id=)(.+?)(?=")',
        'detail_sources': {
            'default': {
                'link': '/user.php?id={}',
                'elements': {
                    'stats': '#content > div > div.sidebar > div:nth-child(4)',
                    'credits': '#bonusdiv > h4',
                    'connected': '#content > div > div.sidebar > div:nth-child(10)'
                }
            }
        },
        'details': {
            'uploaded': {
                'regex': r'Uploaded:\s*([\d.]+ (?:[ZEPTGMK]i)?B)'
            },
            'downloaded': {
                'regex': r'Downloaded:\s*([\d.]+ (?:[ZEPTGMK]i)?B)'
            },
            'share_ratio': {
                'regex': r'Ratio:\s*(∞|[\d,.]+)',
                'handle': handle_share_ratio
            },
            'points': {
                'regex': r'Credits:\s*([\d,.]+)'
            },
            'join_date': {
                'regex': r'Joined:\s*(.+?) ago',
                'handle': handle_join_date
            },
            'seeding': {
                'regex': r'(?<=Seeding: )([\d,]+)'
            },
            'leeching': {
                'regex': r'(?<=Leeching: )([\d,]+)'
            },
            'hr': None
        }
    }


class MainClass(SiteBase):
    URL = 'https://www.cathode-ray.tube/'
    USER_CLASSES = {
        'uploaded': [54975581388800],
        'share_ratio': [1],
        'days': [364]
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

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/login',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method='password',
                succeed_regex=r'Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
                token_regex=r'(?<=name="token" value=").*?(?=")'
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'cinfo': '1920|1080|1|24|-480',
            'iplocked': 0,
            'keeploggedin': [0, 1],
            'submit': 'login',
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

    def get_message(self, entry, config):
        entry['result'] += '(TODO: Message)'  # TODO: Feature not implemented yet

    def get_details(self, entry, config):
        self.get_details_base(entry, config, build_selector())

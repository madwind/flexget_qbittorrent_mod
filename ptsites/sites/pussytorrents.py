from dateutil.parser import parse

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_share_ratio(value):
    if value in ['---', '∞']:
        return '0'
    else:
        return value


def handle_join_date(value):
    return parse(value).date()


def build_selector():
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
                'handle': handle_share_ratio
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


class MainClass(SiteBase):
    URL = 'https://pussytorrents.org/'

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
                url='/user/account/login/',
                method='password',
                succeed_regex=r'Welcome back,</span> <b><a href="/profile/\w+">\w+',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'username': login['username'],
            'password': login['password'],
            'remember_me': 'on',
            'is_forum_login': ''
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

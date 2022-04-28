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
                'handle': handle_share_ratio
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


class MainClass(SiteBase):
    URL = 'https://www.gaytor.rent/'
    USER_CLASSES = {
        'downloaded': [858993459200],
        'share_ratio': [1.05],
        'days': [28]
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
                url='/takelogin.php',
                method='login',
                succeed_regex='Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_by_login(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'username': login['username'],
            'password': login['password'],
            'sw': '1920:1080'
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

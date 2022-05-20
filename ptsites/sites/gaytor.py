from ..schema.site_base import SiteBase, Work, SignState
from ..utils.value_hanlder import handle_infinite, handle_join_date


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

    def build_login_workflow(self, entry, config):
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

    def build_login_data(self, login, last_content):
        return {
            'username': login['username'],
            'password': login['password'],
            'sw': '1920:1080'
        }

    def build_selector(self):
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

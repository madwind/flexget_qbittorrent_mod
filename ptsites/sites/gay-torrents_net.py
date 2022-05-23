import hashlib

from ..schema.site_base import SiteBase, Work, SignState, NetworkState
from ..utils.value_hanlder import handle_infinite


class MainClass(SiteBase):
    URL = 'https://www.gay-torrents.net/'

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
                url='/login.php?do=login',
                method='login',
                succeed_regex=[r'Thank you for logging in, .*?\.</p>'],
                check_state=('network', NetworkState.SUCCEED),
                response_urls=['/login.php?do=login']
            )
        ]

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/latest/',
                method='get',
                succeed_regex=['Log Out'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/latest/']
            )
        ]

    def build_login_data(self, login, last_content):
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

    def build_selector(self):
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

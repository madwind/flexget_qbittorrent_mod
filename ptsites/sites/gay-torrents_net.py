import hashlib

from dateutil.parser import parse

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_share_ratio(value):
    if value in ['---', '∞']:
        return '0'
    else:
        return value


def handle_join_date(value):
    return parse(value).date()


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
                method='password',
                succeed_regex=r'Thank you for logging in, .*?\.</p>',
                check_state=('network', NetworkState.SUCCEED),
                response_urls=['/login.php?do=login']
            )
        ]

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/latest/',
                method='get',
                succeed_regex=r'Log Out',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/latest/']
            )
        ]

    @staticmethod
    def sign_in_data(login, last_content):
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

    @staticmethod
    def build_selector():
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
                    'handle': handle_share_ratio
                },
                'points': {
                    'regex': r'Juices([\d,.]+)'
                },
                'join_date': {
                    'regex': r'Join Date\s*?[\d:]+? (.+?)\s',
                    'handle': handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

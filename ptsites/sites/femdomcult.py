from dateutil.parser import parse

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_join_date(value):
    return parse(value).date()


def handle_share_ratio(value):
    if value == '∞':
        return '0'
    else:
        return value


def build_selector():
    return {
        'user_id': r'<li id="nav_userinfo" class="normal"><a href="user\.php\?id=(\d+)',
        'detail_sources': {
            'default': {
                'do_not_strip': True,
                'link': '/user.php?id={}',
                'elements': {
                    'stats': '#stats_block',
                    'seeding': '#nav_seeding',
                    'leeching': '#nav_leeching',
                    'join date': '#content > div > div.sidebar > div:nth-child(4) > ul > li:nth-child(1)'
                }
            }
        },
        'details': {
            'uploaded': {
                'regex': r'Up</a>:</td>\s*<td><span class="stat">([\d.]+ [ZEPTGMK]?B)'
            },
            'downloaded': {
                'regex': r'Down</a>:</td>\s*<td><span class="stat">([\d.]+ [ZEPTGMK]?B)'
            },
            'share_ratio': {
                'regex': r'Ratio</a>:</td>\s*<td><span class="stat"><span class="r99 infinity">(∞|[\d,.]+)',
                'handle': handle_share_ratio
            },
            'points': {
                'regex': r'Credits</a>:</td>\s*<td><span class="stat">([\d,.]+)'
            },
            'join_date': {
                'regex': r'<span class="time" title="((\w+ ){2}\w+)',
                'handle': handle_join_date
            },
            'seeding': {
                'regex': r'seed: ([\d,]+)'
            },
            'leeching': {
                'regex': r'leech: ([\d,]+)'
            },
            'hr': None
        }
    }


class MainClass(SiteBase):
    URL = 'https://femdomcult.org/'
    USER_CLASSES = {
        'downloaded': [5497558138880],
        'share_ratio': [1.05],
        'days': [56]
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
                url='/login.php',
                method='password',
                succeed_regex='Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/index.php']
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
            'keeplogged': 1,
            'login': 'Login'
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

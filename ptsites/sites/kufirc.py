import re

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
        'user_id': fr'''(?x)(?<= {re.escape('"/user.php?id=')})
                            (. +?)
                            (?= ")''',
        'detail_sources': {
            'default': {
                'do_not_strip': True,
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
                'regex': r'''(?x)Feltöltve:
                                \ 
                                ([\d.] +
                                \ 
                                (?: [ZEPTGMK] i) ?
                                B)'''
            },
            'downloaded': {
                'regex': r'''(?x)Letöltve:
                                \ 
                                ([\d.] +
                                \ 
                                (?: [ZEPTGMK] i) ?
                                B)'''
            },
            'share_ratio': {
                'regex': r'''(?x)Arány:\ <span\ class="r99\ infinity">
                                (∞ | [\d,.] +)''',
                'handle': handle_share_ratio
            },
            'points': {
                'regex': r'''(?x)Bónuszpontok:
                                \s *
                                ([\d,.] +)'''
            },
            'join_date': {
                'regex': r'''(?x)Regisztrált:\ <span\ alt="
                                ((\w + \ ) {2}
                                \w +)''',
                'handle': handle_join_date
            },
            'seeding': {
                'regex': r'''(?x)(?<= Seeding:\ )
                                ([\d,] +)'''
            },
            'leeching': {
                'regex': r'''(?x)(?<= Leeching:\ )
                                ([\d,] +)'''
            },
            'hr': None
        }
    }


class MainClass(SiteBase):
    URL = 'https://kufirc.com/'
    USER_CLASSES = {
        'uploaded': [32985348833280],
        'share_ratio': [2.05],
        'days': [350]
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
                succeed_regex=r'Kilpés',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
                token_regex=r'''(?x)(?<= name="token"\ value=")
                                    . *?
                                    (?= ")'''
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
            'cinfo': '1920|1080|24|-480',
            'iplocked': 0,
            'keeploggedin': [0, 1],
            'submit': 'Bejelentkezés',
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

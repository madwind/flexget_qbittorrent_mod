from ..schema.site_base import SiteBase, Work, SignState


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

    @staticmethod
    def sign_in_data(login, last_content):
        return {
            'username': login['username'],
            'password': login['password'],
            'remember_me': 'on',
            'is_forum_login': ''
        }

    def build_selector(self):
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
                    'handle': self.handle_share_ratio
                },
                'points': None,
                'join_date': {
                    'regex': r'Join Date((\w+ ){3}\w+)',
                    'handle': self.handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

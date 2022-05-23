from ..schema.site_base import SiteBase, Work, SignState
from ..utils.value_hanlder import handle_infinite


class XWT(SiteBase):
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
                succeed_regex=[r'Top 5 Torrents'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def build_login_data(self, login, last_content):
        return {
            'username': login['username'],
            'password': login['password'],
            'returnto': '/'
        }

    def build_selector(self):
        return {
            'detail_sources': {
                'default': {
                    'link': '/browse.php',
                    'elements': {
                        'ratio': '#wel-radio',
                        'up': '#wel-radiok',
                        'down': '#wel-radio2',
                        'active': '#wel-radio3'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Up:\s*([\d.]+ (?i:[ZEPTGMK])B)'
                },
                'downloaded': {
                    'regex': r'(?i)Down:\s*([\d.]+ [ZEPTGMK]B)'
                },
                'share_ratio': {
                    'regex': r'Ratio:\s*(---|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': None,
                'seeding': {
                    'regex': r'Active:\s*(\d+)'
                },
                'leeching': {
                    'regex': r'Active:\s*\d+\s*(\d+)'
                },
                'hr': None
            }
        }

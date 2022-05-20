import re

from ..schema.ocelot import Ocelot
from ..schema.site_base import Work, SignState, NetworkState


class MainClass(Ocelot):
    URL = 'https://filelist.io/'
    USER_CLASSES = {
        'downloaded': [45079976738816],
        'share_ratio': [5],
        'days': [1460]
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
                            'password': {'type': 'string'},
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
                url='/login.php',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/takelogin.php',
                method='login',
                succeed_regex='Hello, <a .+?</a>',
                response_urls=['/my.php'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
            )
        ]

    def build_login_data(self, login, last_content):
        return {
            'validator': re.search("(?<='validator' value=').*(?=')", last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'unlock': 1
        }

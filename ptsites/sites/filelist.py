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
                method='password',
                succeed_regex='Hello, <a .+?</a>',
                response_urls=['/my.php'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                validator_regex="(?<='validator' value=').*(?=')"
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        validator = re.search(work.validator_regex, last_content).group()
        data = {
            'validator': validator,
            'username': login['username'],
            'password': login['password'],
            'unlock': 1
        }
        return self._request(entry, 'post', work.url, data=data)

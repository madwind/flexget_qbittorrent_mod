import re

from ..base.request import NetworkState, check_network_state
from ..base.sign_in import  SignState
from ..base.work import Work
from ..base.sign_in import check_final_state
from ..utils.net_utils import get_module_name
from ..schema.ocelot import Ocelot


class MainClass(Ocelot):
    URL = 'https://filelist.io/'
    USER_CLASSES = {
        'downloaded': [45079976738816],
        'share_ratio': [5],
        'days': [1460]
    }

    @classmethod
    def sign_in_build_schema(cls):
        return {
            get_module_name(cls): {
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

    def sign_in_build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login.php',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/takelogin.php',
                method=self.sign_in_by_login,
                succeed_regex=['Hello, <a .+?</a>'],
                response_urls=['/my.php'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
            )
        ]

    def sign_in_build_login_data(self, login, last_content):
        return {
            'validator': re.search("(?<='validator' value=').*(?=')", last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'unlock': 1
        }

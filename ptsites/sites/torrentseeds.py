import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.unit3d import Unit3D
from ..utils.net_utils import get_module_name


class MainClass(Unit3D):
    URL: Final = 'https://www.torrentseeds.org'
    USER_CLASSES: Final = {
        'uploaded': [109951162777600],
        'days': [365]
    }

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'},
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

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        m = re.search(r'name="(?P<name>.+?)" value="(?P<value>.+?)" />\s*<button type="submit"', last_content)
        return {
            '_token': re.search(r'(?<=name="_token" value=").+?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
            '_captcha': re.search(r'(?<=name="_captcha" value=").+?(?=")', last_content).group(),
            '_username': '',
            m.group('name'): m.group('value'),
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method=self.sign_in_by_login,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                response_urls=['', '/pages/1'],
            )
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[('<a href="https://www.torrentseeds.org/users/(.*?)">', 1)],
                assert_state=(check_final_state, SignState.SUCCEED),
                use_last_content=True,
                is_base_content=True,
                response_urls=['', '/pages/1']
            )
        ]

import re

from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.unit3d import Unit3D
from ..utils.net_utils import get_module_name


class MainClass(Unit3D):
    URL = 'https://www.torrentseeds.org/'
    USER_CLASSES = {
        'uploaded': [109951162777600],
        'days': [365]
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
                            'password': {'type': 'string'}
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
                url='/login',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method=self.sign_in_by_login,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['', '/pages/1'],
            )
        ]

    def sign_in_build_login_data(self, login, last_content):
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

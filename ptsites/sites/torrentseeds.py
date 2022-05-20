import re

from ..schema.site_base import SignState, Work, NetworkState
from ..schema.unit3d import Unit3D


class MainClass(Unit3D):
    URL = 'https://www.torrentseeds.org/'
    USER_CLASSES = {
        'uploaded': [109951162777600],
        'days': [365]
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

    def build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method='login',
                succeed_regex='Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/pages/1'],
            )
        ]

    def build_login_data(self, login, last_content):
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

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector

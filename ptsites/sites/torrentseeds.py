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
                succeed_regex='Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/pages/1'],
                token_regex=r'(?<=name="_token" value=").+?(?=")',
                captcha_regex=r'(?<=name="_captcha" value=").+?(?=")',
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        r = re.compile(r'name="(?P<name>.+?)" value="(?P<value>.+?)" />\s*<button type="submit"')
        m = re.search(r, last_content)
        data = {
            '_token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
            '_captcha': re.search(work.captcha_regex, last_content).group(),
            '_username': '',
            m.group('name'): m.group('value'),
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector

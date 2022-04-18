import re
from urllib.parse import urljoin

from ..schema.discuz import Discuz
from ..schema.site_base import Work, NetworkState, SignState
from ..utils.google_auth import GoogleAuth


class MainClass(Discuz):
    URL = 'https://skyeysnow.com/'
    USER_CLASSES = {
        'points': [1000000]
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
                url='/login.php',
                method='login',
                check_state=('network', NetworkState.SUCCEED),
                login_url_regex='(?<=action=").*?(?=")',
                formhash_regex='(?<="formhash" value=").*(?=")'
            )
        ]

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<a.*?title="访问我的空间">.*?</a>',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def sign_in_by_login(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return

        secret_key = login.get('secret_key')
        username, password = login['username'], login['password']

        if secret_key:
            totp_code = GoogleAuth.calc(secret_key)
            username += '@' + totp_code

        login_url = urljoin(entry['url'], re.search(work.login_url_regex, last_content).group())
        work.response_urls = [login_url]
        formhash = re.search(work.formhash_regex, last_content).group()
        data = {
            'formhash': formhash,
            'referer': '/',
            'loginfield': 'username',
            'username': username,
            'password': password,
            'loginsubmit': 'true'
        }
        return self._request(entry, 'post', login_url, data=data, verify=False)

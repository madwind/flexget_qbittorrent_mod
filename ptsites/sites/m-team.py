import re
from urllib.parse import urljoin

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import Work, NetworkState, SignState
from ..utils import net_utils, google_auth


class MainClass(NexusPHP):
    URL = 'https://kp.m-team.cc/'
    USER_CLASSES = {
        'downloaded': [2147483648000, 3221225472000],
        'share_ratio': [7, 9],
        'days': [168, 224]
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
                            'secret_key': {'type': 'string'}
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
                method='verify',
                succeed_regex=['歡迎回來'],
                check_state=('final', SignState.SUCCEED),
                response_urls=['/verify.php?returnto=', '/index.php'],
                is_base_content=True,
                verify_url='/verify.php?returnto=',
            )
        ]

    def build_login_data(self, login, last_content):
        return {
            'username': login['username'],
            'password': login['password'],
        }

    def sign_in_by_verify(self, entry, config, work, last_content):
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return

        login_response = self.sign_in_by_login(entry, config, work, last_content)

        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        verify_url = urljoin(entry['url'], work.verify_url)
        if login_response.url.startswith(verify_url):
            content = net_utils.decode(login_response)
            attempts = re.search('您還有(\\d+)次嘗試機會，否則該IP將被禁止訪問。', content)
            if attempts:
                times = attempts.group(1)
                if times == '30':
                    google_code = google_auth.calc(login['secret_key'])
                    data = {
                        'otp': (None, google_code)
                    }
                    return self._request(entry, 'post', verify_url, files=data)
                else:
                    entry.fail_with_prefix('{} with google_auth'.format(attempts.group()))
            else:
                entry.fail_with_prefix('Attempts text not found!  with google_auth')
        return login_response

    def get_message(self, entry, config):
        self.get_nexusphp_message(entry, config)
        system_message_url = '/messages.php?action=viewmailbox&box=-2'
        self.get_nexusphp_message(entry, config, messages_url=system_message_url)

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

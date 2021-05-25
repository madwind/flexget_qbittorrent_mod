import re
from urllib.parse import urljoin

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import Work, NetworkState, SignState
from ..utils.google_auth import GoogleAuth
from ..utils.net_utils import NetUtils


class MainClass(NexusPHP):
    URL = 'https://kp.m-team.cc/'
    USER_CLASSES = {
        'downloaded': [2147483648000, 3221225472000],
        'share_ratio': [7, 9],
        'days': [168, 224]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/takelogin.php',
                method='login',
                succeed_regex='歡迎回來',
                check_state=('final', SignState.SUCCEED),
                response_urls=['/verify.php?returnto=', '/index.php'],
                is_base_content=True,
                verify_url='/verify.php?returnto=',
            )
        ]

    def sign_in_by_login(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return

        data = {
            'username': login['username'],
            'password': login['password'],
        }

        login_response = self._request(entry, 'post', work.url, data=data)

        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return

        if login_response.url.startswith(urljoin(entry['url'], work.verify_url)):
            content = NetUtils.decode(login_response)
            attempts = re.search('您還有(\\d+)次嘗試機會，否則該IP將被禁止訪問。', content)
            if attempts:
                times = attempts.group(1)
                if times == '30':
                    google_code = GoogleAuth.calc(login['secret_key'])
                    data = {
                        'otp': (None, google_code)
                    }
                    return self._request(entry, 'post', work.verify_url, files=data)
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
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

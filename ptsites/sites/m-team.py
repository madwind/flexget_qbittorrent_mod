import re

from loguru import logger

from ..nexusphp import NexusPHP
from ..site_base import SignState
from ..utils.google_auth import GoogleAuth

# auto_sign_in
LOGIN_URL = 'https://pt.m-team.cc/takelogin.php'
URL = 'https://pt.m-team.cc/index.php'
VERIFY_URL = 'https://pt.m-team.cc/verify.php?returnto='
SUCCEED_REGEX = '歡迎回來'
SYSTEM_MESSAGE_URL = '/messages.php?action=viewmailbox&box=-2'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = 'https://{}/{}&https=1'.format(base_url, download_page)

    def sign_in_by_get(self, entry, config):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail('Login data not found!')
            return

        data = {
            'username': login['username'],
            'password': login['password'],
        }

        response = self._request(entry, 'post', LOGIN_URL, data=data)

        login_state = self.check_net_state(entry, response, URL)
        if login_state:
            entry.fail('Login failed!')

        use_google_auth = False
        if response.url.startswith(VERIFY_URL):
            content = self._decode(response)
            attempts = re.search('您還有(\\d+)次嘗試機會，否則該IP將被禁止訪問。', content)
            if attempts:
                times = attempts.group(1)
                if times == '30':
                    google_code = GoogleAuth.calc(login['secret_key'])
                    data = {
                        'otp': (None, google_code)
                    }
                    entry['base_response'] = response = self._request(entry, 'post', VERIFY_URL, files=data)
                    use_google_auth = True
                else:
                    entry.fail('{} with google_auth'.format(attempts.group()))
            else:
                entry.fail('Attempts text not found!  with google_auth')
        self.final_check(entry, response, entry['url'])
        if use_google_auth:
            entry['result'] = entry['result'] + ' with google_auth'

    def check_net_state(self, entry, response, original_url):
        if not response:
            entry.fail(
                entry['prefix'] + '=> ' + SignState.NETWORK_ERROR.value.format(url=original_url,
                                                                               error='Response is None'))
            return SignState.NETWORK_ERROR

        if response.url not in [original_url, VERIFY_URL]:
            entry.fail(entry['prefix'] + '=> ' + SignState.URL_REDIRECT.value.format(original_url, response.url))
            return SignState.URL_REDIRECT

    def get_message(self, entry, config):
        self.get_nexusphp_message(entry, config)
        self.get_nexusphp_message(entry, config, messages_url=SYSTEM_MESSAGE_URL)

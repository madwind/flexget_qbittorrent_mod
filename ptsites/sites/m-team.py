import re
from urllib.parse import urljoin

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState
from ..utils.google_auth import GoogleAuth

# auto_sign_in
BASE_URL = 'https://pt.m-team.cc/'
LOGIN_URL = urljoin(BASE_URL, '/takelogin.php')
URL = urljoin(BASE_URL, '/index.php')
VERIFY_URL = urljoin(BASE_URL, '/verify.php?returnto=')
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
    def build_reseed(entry, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = urljoin(BASE_URL, download_page + '&https=1')

    def get_message(self, entry, config):
        self.get_nexusphp_message(entry, config)
        self.get_nexusphp_message(entry, config, messages_url=SYSTEM_MESSAGE_URL)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

    def sign_in_by_get(self, entry, config):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return

        data = {
            'username': login['username'],
            'password': login['password'],
        }

        entry['base_response'] = response = self._request(entry, 'post', LOGIN_URL, data=data)

        login_state = self.check_net_state(entry, response, URL)
        if login_state:
            return

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
                    entry.fail_with_prefix('{} with google_auth'.format(attempts.group()))
            else:
                entry.fail_with_prefix('Attempts text not found!  with google_auth')
        self.final_check(entry, response, entry['url'])
        if use_google_auth:
            entry['result'] = entry['result'] + ' with google_auth'

    def check_net_state(self, entry, response, original_url):
        if not response:
            entry.fail_with_prefix(SignState.NETWORK_ERROR.value.format(url=original_url, error='Response is None'))
            return SignState.NETWORK_ERROR

        if response.url not in [original_url, VERIFY_URL]:
            entry.fail_with_prefix(SignState.URL_REDIRECT.value.format(original_url, response.url))
            return SignState.URL_REDIRECT

import re

from ..site_base import SignState
from ..utils.google_auth import GoogleAuth
from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://pt.m-team.cc/'
VERIFY_URL = 'https://pt.m-team.cc/verify.php?returnto=%2F'
SUCCEED_REGEX = '歡迎回來'
SYSTEM_MESSAGE_URL = '/messages.php?action=viewmailbox&box=-2'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        if isinstance(entry['site_config'], str):
            SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)
        else:
            entry['secret_key'] = entry['site_config']['secret_key']
            entry['site_config'] = entry['site_config']['cookie']
            SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = 'https://{}/{}&https=1'.format(base_url, download_page)

    def sign_in_by_get(self, entry, config):
        entry['base_response'] = response = self._request(entry, 'get', entry['url'])
        net_state = self.check_net_state(entry, response, entry['url'])
        use_google_auth = False
        if net_state == SignState.URL_REDIRECT:
            if response.url.startswith(VERIFY_URL):
                content = self._decode(response)
                attempts = re.search('您還有30次嘗試機會，否則該IP將被禁止訪問。', content)
                if attempts:
                    google_code = GoogleAuth.calc(entry['secret_key'])
                    data = {
                        'otp': (None, google_code)
                    }
                    entry['base_response'] = response = self._request(entry, 'post', VERIFY_URL, files=data)

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

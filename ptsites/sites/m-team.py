import re

from ..utils.google_auth import GoogleAuth
from ..executor import Executor, SignState

# auto_sign_in
URL = 'https://pt.m-team.cc/'
VERIFY_URL = 'https://pt.m-team.cc/verify.php'
SUCCEED_REGEX = '歡迎回來'
MESSAGE_URL = 'https://pt.m-team.cc/messages.php?action=viewmailbox&box=-2'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        if isinstance(entry['site_config'], str):
            Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)
        else:
            entry['secret_key'] = entry['site_config']['secret_key']
            entry['site_config'] = entry['site_config']['cookie']
            Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = 'https://{}/{}&https=1'.format(base_url, download_page)

    def sign_in_by_get(self, entry, config):
        response = self._request(entry, 'get', entry['url'], headers=entry['headers'])
        net_state = self.check_net_state(entry, response, entry['url'])
        if net_state == SignState.URL_REDIRECT:
            if response.url.startswith(VERIFY_URL):
                content = self._decode(response)
                attempts = re.search('您還有30次嘗試機會，否則該IP將被禁止訪問。', content)
                if attempts:
                    google_code = GoogleAuth.calc(entry['secret_key'])
                    data = {
                        'otp': (None, google_code)
                    }
                    response = self._request(entry, 'post', VERIFY_URL, files=data)

        self.final_check(entry, response, entry['url'])
        entry['result'] = entry['result'] + ' with google_auth'

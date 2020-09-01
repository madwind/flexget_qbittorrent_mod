import re
from urllib.parse import urljoin

from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://www.skyey2.com/login.php'
LOGIN_URL_REGEX = '(?<=action=").*?(?=")'
FORMHASH_REGEX = '(?<="formhash" value=").*(?=")'
SUCCEED_REGEX = '欢迎您回来，.*?(?=，)'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers

    def sign_in(self, entry, config):
        login = entry['site_config'].get('login')
        response = self._request(entry, 'get', URL, headers=entry['headers'])
        state = self.check_net_state(entry, response, URL)
        if state:
            return
        content = self._decode(response)
        login_url = urljoin(URL, re.search(LOGIN_URL_REGEX, content).group())
        formhash = re.search(FORMHASH_REGEX, content).group()
        data = {
            'formhash': formhash,
            'referer': '/',
            'loginfield': 'username',
            'username': login['username'],
            'password': login['password'],
            'loginsubmit': 'true'
        }
        response = self._request(entry, 'post', login_url, data=data)
        self.final_check(entry, response, login_url)

    def get_message(self, entry, config):
        pass

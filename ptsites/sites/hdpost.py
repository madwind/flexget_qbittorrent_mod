import json

from ..executor import Executor

# auto_sign_in
BASE_URL = 'https://hdpost.top/'
LOGIN_URL = 'https://hdpost.top/api/auth/signin'
URL = 'https://hdpost.top/api/check'
SUCCEED_REGEX = '"keepDays":\\d+|YOU_ALREADY_CHECK_IN'


# site_config
# login:
#    usernameOrEmail: 'xxxxx'
#    password: 'xxxxxxxx'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'user-agent': config.get('user-agent'),
            'referer': BASE_URL,
        }
        entry['headers'] = headers

    def do_sign_in(self, entry, config):
        login = entry['site_config'].get('login')
        if login:
            response = self._request(entry, 'post', LOGIN_URL, headers=entry['headers'], data=login)
            if response.status_code == 200:
                response = self._request(entry, 'put', URL)
                self.final_check(entry, response, URL)
            else:
                entry['result'] = 'login failed'
                entry.fail(entry['result'])
        else:
            entry['result'] = 'login data not found'
            entry.fail(entry['result'])

import json

from loguru import logger

from ..executor import Executor, SignState

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
            login_response = self._request(entry, 'post', LOGIN_URL, headers=entry['headers'], data=login)
            if login_response.status_code == 200:
                response = self._request(entry, 'put', URL)
                self.final_check(entry, response, URL)
            else:
                entry['result'] = 'login failed'
                entry.fail(entry['result'])
        else:
            entry['result'] = 'login data not found'
            entry.fail(entry['result'])

    def check_net_state(self, entry, response, original_url, is_message=False):
        if not response and response.status_code != 422:
            logger.info('noonono')
            if not is_message:
                if not entry['result'] and not is_message:
                    entry['result'] = SignState.NETWORK_ERROR.value.format('Response is None')
                entry.fail(entry['result'])
            return SignState.NETWORK_ERROR

        if response.url != original_url:
            if not is_message:
                entry['result'] = SignState.URL_REDIRECT.value.format(original_url, response.url)
                entry.fail(entry['result'])
            return SignState.URL_REDIRECT

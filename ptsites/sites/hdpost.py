from ..schema.meantorrent import MeanTorrent

# auto_sign_in
from ..schema.site_base import SignState

BASE_URL = 'https://hdpost.top/'
LOGIN_URL = 'https://hdpost.top/api/auth/signin'
URL = 'https://hdpost.top/api/check'
SUCCEED_REGEX = '"keepDays":\\d+|YOU_ALREADY_CHECK_IN'


# site_config
# login:
#    usernameOrEmail: 'xxxxx'
#    password: 'xxxxxxxx'


class MainClass(MeanTorrent):
    @staticmethod
    def build_sign_in(entry, config):
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'user-agent': config.get('user-agent'),
            'referer': BASE_URL,
        }
        entry['headers'] = headers

    def sign_in(self, entry, config):
        login = entry['site_config'].get('login')
        if login:
            login_response = self._request(entry, 'post', LOGIN_URL, data=login)
            if login_response and login_response.status_code == 200:
                entry['base_response'] = base_response = self._request(entry, 'put', URL)
                self.final_check(entry, base_response, URL)
            else:
                entry.fail('Login failed.')
        else:
            entry.fail('Login data not found.')

    def check_net_state(self, entry, response, original_url):
        if not response and response.status_code != 422:
            entry.fail(
                entry['prefix'] + '=> ' + SignState.NETWORK_ERROR.value.format(url=original_url,
                                                                               error='Response is None'))
            return SignState.NETWORK_ERROR

        if response.url != original_url:
            entry.fail(entry['prefix'] + '=> ' + SignState.URL_REDIRECT.value.format(original_url, response.url))
            return SignState.URL_REDIRECT

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

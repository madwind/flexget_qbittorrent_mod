from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState
from ..schema.site_base import SiteBase

# auto_sign_in
BASE_URL = 'https://www.haidan.video/index.php'
URL = 'https://www.haidan.video/signin.php'
SUCCEED_REGEX = '(?<=value=")已经打卡(?=")'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX, base_url=BASE_URL)

    def check_net_state(self, entry, response, original_url):
        if not response:
            entry.fail_with_prefix(SignState.NETWORK_ERROR.value.format(url=original_url, error='Response is None'))
            return SignState.NETWORK_ERROR

        if response.url not in [BASE_URL, URL, original_url]:
            entry.fail_with_prefix(SignState.URL_REDIRECT.value.format(original_url, response.url))
            return SignState.URL_REDIRECT

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#head > div.top-panel.special-border > div > div:nth-child(2)',
                        'table': 'body > div.mainroute > div.mainpanel.special-border > table > tbody > tr > td > table'
                    }
                }
            },
            'details': {
                'hr': None
            }
        })
        return selector

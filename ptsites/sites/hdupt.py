from ..schema.site_base import SiteBase
from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState

# auto_sign_in
BASE_URL = 'https://pt.hdupt.com/'
BASE_SUCCEED_REGEX = '<span id="yiqiandao">\\[已签到\\]</span>'
URL = 'https://pt.hdupt.com/added.php'
SUCCEED_REGEX = '\\d+'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX, base_url=BASE_URL)

    def sign_in(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', entry['base_url'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, entry['base_url'],
                                                               regex=BASE_SUCCEED_REGEX)
        if sign_in_state != SignState.NO_SIGN_IN:
            return
        data = {
            'action': (None, 'qiandao')
        }
        response = self._request(entry, 'post', URL, files=data)
        self.final_check(entry, response, URL)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details']['hr'] = None
        return selector

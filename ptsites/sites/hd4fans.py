import re

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase, SignState

# auto_sign_in
BASE_URL = 'https://pt.hd4fans.org/'
URL = 'https://pt.hd4fans.org/checkin.php'
SUCCEED_REGEX = '<span id="checkedin">\\[签到成功\\]</span>'
DATA = {
    'fixed': {
        'action': 'checkin'
    }
}


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX, base_url=BASE_URL)
        entry['data'] = DATA

    def sign_in(self, entry, config):
        self.sign_in_by_post_data(entry, config)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

    def sign_in_by_post_data(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', entry['base_url'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, entry['base_url'])
        if sign_in_state != SignState.NO_SIGN_IN:
            return
        data = {}
        for key, regex in entry.get('data', {}).items():
            if key == 'fixed':
                self.dict_merge(data, regex)
            else:
                value_search = re.search(regex, base_content)
                if value_search:
                    data[key] = value_search.group()
                else:
                    entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, entry['url']))
                    return
        checkin_response = self._request(entry, 'post', entry['url'], data=data)
        checkin_response_state = self.check_net_state(entry, checkin_response, entry['url'])
        if checkin_response_state:
            return
        response = self._request(entry, 'get', entry['base_url'])
        self.final_check(entry, response, entry['base_url'])

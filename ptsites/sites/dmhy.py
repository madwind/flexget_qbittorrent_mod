import random
import re

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState

# auto_sign_in
BASE_URL = 'https://u2.dmhy.org/'
URL = 'https://u2.dmhy.org/showup.php?action=show'
USERNAME_REGEX = '<bdo dir=\'ltr\'>{username}</bdo>'
SUCCEED_REGEX = '.{120,200}奖励UCoin: <b>\\d+|<a href="showup.php">已签到</a>'
DATA = {
    'regex_keys': ['<input type="submit" name="(captcha_.*?)" value="(.*?)" />'],
    'req': '<input type="hidden" name="req" value="(.*?)" />',
    'hash': '<input type="hidden" name="hash" value="(.*?)" />',
    'form': '<input type="hidden" name="form" value="(.*?)" />'
}


# site_config
#    username: 'xxxxx'
#    cookie: 'xxxxxxxx'
#    comment: 'xxxxxx'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        site_config = entry['site_config']
        entry['url'] = URL
        entry['succeed_regex'] = USERNAME_REGEX.format(username=site_config.get('username')) + SUCCEED_REGEX
        entry['base_url'] = BASE_URL
        headers = {
            'cookie': site_config.get('cookie'),
            'user-agent': config.get('user-agent'),
            'referer': BASE_URL
        }
        entry['headers'] = headers
        entry['data'] = DATA

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': ('UCoin.*?([\\d,.]+)\\(([\\d,.]+)\\)', 2)
                },
                'seeding': {
                    'regex': ('客户端.*?(\\d+).*?(\\d+).*?(\\d+)', 2)
                },
                'leeching': {
                    'regex': ('客户端.*?(\\d+).*?(\\d+).*?(\\d+)', 3)
                },
                'hr': None
            }
        })
        return selector

    def sign_in(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', entry['url'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, entry['url'])
        if sign_in_state != SignState.NO_SIGN_IN:
            return
        data = {}
        for key, regex in entry.get('data', {}).items():
            if key == 'regex_keys':
                for regex_key in regex:
                    regex_key_search = re.findall(regex_key, base_content, re.DOTALL)
                    if regex_key_search:
                        regex_result = regex_key_search[random.randint(0, len(regex_key_search) - 1)]
                        data[regex_result[0]] = regex_result[1]
                    else:
                        entry.fail_with_prefix('Cannot find regex_key: {}, url: {}'.format(regex_key, entry['url']))
                        return
            else:
                value_search = re.search(regex, base_content, re.DOTALL)
                if value_search:
                    data[key] = value_search.group(1)
                else:
                    entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, entry['url']))
                    return
        site_config = entry['site_config']
        data['message'] = site_config.get('comment')
        post_answer_response = self._request(entry, 'post', entry['url'], data=data)
        post_answer_net_state = self.check_net_state(entry, post_answer_response, entry['url'])
        if post_answer_net_state:
            return
        response = self._request(entry, 'get', entry['url'])
        self.final_check(entry, response, entry['url'])

    def check_sign_in_state(self, entry, response, original_url, regex=None):
        net_state = self.check_net_state(entry, response, original_url)
        if net_state:
            return net_state, None

        content = self._decode(response)
        succeed_regex = regex if regex else entry.get('succeed_regex')

        succeed_list = re.findall(succeed_regex, content, re.DOTALL)
        if succeed_list:
            entry['result'] = re.sub('<.*?>|&shy;', '', succeed_list[-1])
            return SignState.SUCCEED, content
        return SignState.NO_SIGN_IN, content

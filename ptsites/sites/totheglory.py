from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
BASE_URL = 'https://totheglory.im/'
URL = 'https://totheglory.im/signed.php'
SUCCEED_REGEX = '<b style="color:green;">已签到</b>|您已连续签到\\d+天，奖励\\d+积分，明天继续签到将获得\\d+积分奖励。'
DATA = {
    'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
    'signed_token': '(?<=signed_token: ").*(?=")'
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
        selector['details_content'][
            'details_bar'] = 'body > table:nth-child(3) > tbody > tr > td > table > tbody > tr > td:nth-child(1)'
        selector['details_content'][
            'details_table'] = '#main_table > tbody > tr:nth-child(1) > td > table > tbody > tr > td > table > tbody'
        selector['details']['points'] = {
            'regex': '(积分).*?([\\d,.]+)',
            'group': 2,
            'default': 0
        }
        selector['details']['seeding'] = {
            'regex': '(做种活动).*?(\\d+)',
            'group': 2,
            'default': 0
        }
        selector['details']['leeching'] = {
            'regex': '(做种活动).*?(\\d+)\\D+(\\d+)',
            'group': 3,
            'default': 0
        }
        return selector

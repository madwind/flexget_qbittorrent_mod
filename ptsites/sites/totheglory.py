from ..schema.site_base import SiteBase
from ..schema.nexusphp import NexusPHP

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
        self.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'body > table:nth-child(3) > tbody > tr > td > table > tbody > tr > td:nth-child(1)',
                        'table': '#main_table > tbody > tr:nth-child(1) > td > table > tbody > tr > td > table > tbody'
                    }
                }
            },
            'details': {
                'downloaded': {
                    'regex': ('(下[载載]量|Downloaded).+?([\\d.]+ ?[ZEPTGMk]?i?B)', 2),
                    'handle': self.handle_size
                },
                'uploaded': {
                    'regex': ('(上[传傳]量|Uploaded).+?([\\d.]+ ?[ZEPTGMk]?i?B)', 2),
                    'handle': self.handle_size
                },
                'share_ratio': {
                    'regex': '分享率.*?(Inf\\.|[\\d.]+)',
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': '积分.*?([\\d,.]+)'
                },
                'seeding': {
                    'regex': '做种活动.*?(\\d+)'
                },
                'leeching': {
                    'regex': '做种活动.*?\\d+\\D+(\\d+)'
                },
                'hr': {
                    'regex': 'HP.*?(\\d+)',
                    'handle': self.handle_hr
                }
            }
        })
        return selector

    def handle_size(self, size):
        return size.upper()

    def handle_share_ratio(self, value):
        if value == 'Inf.':
            return '0'
        else:
            return value

    def handle_hr(self, hr):
        return str(15 - int(hr))

from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://ptsbao.club/'
SUCCEED_REGEX = '欢迎回家'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details']['hr'] = {
            'regex': '(H&R).*?(\\d+)',
            'group': 2,
        }
        return selector

from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://pt.keepfrds.com/'
SUCCEED_REGEX = '欢迎回来'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details_content'][
            'details_bar'] = '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(1)'
        return selector

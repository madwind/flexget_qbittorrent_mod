from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://pt.sjtu.edu.cn/'
SUCCEED_REGEX = '魔力值 \\(\\d+\\)'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details_content']['details_bar'] = None
        selector['details_content'][
            'details_table'] = 'body > table.mainouter > tbody > tr:nth-child(2) > td > table:nth-child(5) > tbody > tr > td > table > tbody'
        selector['details']['seeding'] = None
        selector['details']['leeching'] = None
        return selector

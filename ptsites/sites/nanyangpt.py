from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://nanyangpt.com/'
SUCCEED_REGEX = '魔力豆 \\(.*?\\)'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details_content']['details_bar'] = None
        selector['details']['seeding'] = None
        selector['details']['leeching'] = None
        return selector

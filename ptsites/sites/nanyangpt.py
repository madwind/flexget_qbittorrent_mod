from ..schema.site_base import SiteBase
from ..schema.nexusphp import NexusPHP

# auto_sign_in
URL = 'https://nanyangpt.com/'
SUCCEED_REGEX = '魔力豆 \\(.*?\\)'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['detail_sources'][0]['elements']['bar'] = '#userlink > ul > div:nth-child(3)'
        selector['details']['hr'] = None
        return selector

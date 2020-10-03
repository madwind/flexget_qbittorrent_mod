from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'http://avgv.cc/'
SUCCEED_REGEX = '歡迎回來'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

from ..nexusphp import NexusPHP
from ..site_base import SiteBase

# auto_sign_in
URL = 'http://avgv.cc/'
SUCCEED_REGEX = '歡迎回來'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

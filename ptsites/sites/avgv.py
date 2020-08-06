from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'http://avgv.cc/'
SUCCEED_REGEX = '歡迎回來'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        NexusPHP.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX)

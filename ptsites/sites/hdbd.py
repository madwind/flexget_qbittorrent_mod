from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://pt.hdbd.us/'
SUCCEED_REGEX = '伊甸园 PT Torrents'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        NexusPHP.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX)

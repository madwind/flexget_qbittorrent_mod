from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://nanyangpt.com/'
SUCCEED_REGEX = '魔力豆 \\(.*?\\)'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        NexusPHP.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX)

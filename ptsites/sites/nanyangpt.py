from ..executor import Executor

# auto_sign_in
URL = 'https://nanyangpt.com/'
SUCCEED_REGEX = '魔力豆 \\(.*?\\)'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)

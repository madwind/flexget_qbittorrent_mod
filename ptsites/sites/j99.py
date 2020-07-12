from ..executor import Executor

# auto_sign_in
URL = 'https://pt.j99.info/'
SUCCEED_REGEX = '欢迎回来'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)

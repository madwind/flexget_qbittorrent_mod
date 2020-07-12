from ..executor import Executor

# auto_sign_in
URL = 'https://pt.sjtu.edu.cn/'
SUCCEED_REGEX = '魔力值 \\(\\d+\\)'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)

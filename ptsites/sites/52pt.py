from ..executor import Executor

# auto_sign_in
URL = 'https://52pt.site/bakatest.php'
SUCCEED_REGEX = '连续.*天签到,获得.*点魔力值|今天已经签过到了\\(已连续.*天签到\\)'
WRONG_REGEX = '回答错误,失去 1 魔力值,这道题还会再考一次'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX, wrong_regex=WRONG_REGEX)

    def do_sign_in(self, entry, config):
        self.sign_in_by_question(entry, config)

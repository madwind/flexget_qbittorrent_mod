from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://chdbits.co/bakatest.php'
SUCCEED_REGEX = '签到成功,获得\\d+点魔力值|连续\\d+天签到,获得\\d+点魔力值|今天已经签过到了\\(已连续\\d+天签到\\)'
WRONG_REGEX = '回答错误,失去 1 魔力值,这道题还会再考一次'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        NexusPHP.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX, wrong_regex=WRONG_REGEX)

    def sign_in(self, entry, config):
        self.sign_in_by_question(entry, config)

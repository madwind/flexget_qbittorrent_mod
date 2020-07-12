from ..executor import Executor

# auto_sign_in
URL = 'https://pterclub.com/attendance-ajax.php'
SUCCEED_REGEX = '这是您的第 .* 次签到，已连续签到 .* 天。.*本次签到获得 .* 克猫粮。|您今天已经签到过了，请勿重复刷新。'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)

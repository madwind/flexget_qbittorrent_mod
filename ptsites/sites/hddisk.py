from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://hddisk.life/attendance.php'
SUCCEED_REGEX = '这是您的第 .* 次签到，已连续签到 .* 天，本次签到获得 .* 个魔力值。|您今天已经签到过了，请勿重复刷新。'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details']['hr'] = {
            'regex': '(H&R).*?(\\d+)',
            'group': 2,
        }
        return selector

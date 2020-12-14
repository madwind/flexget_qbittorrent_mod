from ..schema.site_base import SiteBase
from ..schema.nexusphp import NexusPHP

# auto_sign_in
URL = 'https://lemonhd.org/attendance.php'
SUCCEED_REGEX = '这是您的第 .* 次签到，已连续签到 .* 天，本次签到获得 .* 魔力值。|您今天已经签到过了，请勿重复刷新。'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

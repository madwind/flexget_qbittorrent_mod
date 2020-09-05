from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://www.nicept.net/attendance.php'
SUCCEED_REGEX = '這是您的第 .* 次簽到，已連續簽到 .* 天，本次簽到獲得 .* 個魔力值。|您今天已經簽到過了，請勿重複刷新。'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

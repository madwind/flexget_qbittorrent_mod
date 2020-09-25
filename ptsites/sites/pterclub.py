from ..schema.site_base import SiteBase
from ..schema.nexusphp import NexusPHP

# auto_sign_in
BASE_URL = 'https://pterclub.com/'
URL = 'https://pterclub.com/attendance-ajax.php'
SUCCEED_REGEX = '签到已得\\d+|这是您的第 .* 次签到，已连续签到 .* 天。.*本次签到获得 .* 克猫粮。|您今天已经签到过了，请勿重复刷新。'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX, base_url=BASE_URL)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details']['points'] = {'regex': '猫粮.*?([\\d,.]+)'}
        return selector

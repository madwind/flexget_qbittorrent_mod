from ..schema.nexusphp import AttendanceHR
from ..utils.net_utils import NetUtils


class MainClass(AttendanceHR):
    URL = 'https://hdhome.org/'
    USER_CLASSES = {
        'downloaded': [8796093022208],
        'share_ratio': [5.5],
        'points': [1000000],
        'days': [70]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': '做种积分([\\d.,]+)',
                }
            }
        })
        return selector

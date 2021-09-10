from ..schema.nexusphp import Attendance
from ..utils.net_utils import NetUtils


class MainClass(Attendance):
    URL = 'https://club.hares.top/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4.0, 5.5],
        'days': [175, 364]
    }

    def build_selector(self):
        selector = super(Attendance, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': None,
                'points': {
                    'regex': ('(奶糖).*?([\\d,.]+)', 2)
                },
            }
        })
        return selector

from ..schema.nexusphp import VisitHR
from ..utils.net_utils import NetUtils


class MainClass(VisitHR):
    URL = 'https://tjupt.org/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def build_selector(self):
        selector = super(VisitHR, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': {
                    'regex': 'HnR.*?(\\d+)',
                    'handle': self.handle_hr
                }
            }
        })
        return selector

    def handle_hr(self, hr):
        return str(100 - int(hr))

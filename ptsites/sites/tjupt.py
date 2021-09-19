from ..schema.nexusphp import VisitHR
from ..utils.net_utils import NetUtils


class MainClass(VisitHR):
    URL = 'https://tjupt.org/'
    USER_CLASSES = {
        'uploaded': [5368709120000, 53687091200000],
        'days': [336, 924]
    }

    def build_selector(self):
        selector = super(VisitHR, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'downloaded': None,
                'share_ratio': None,
                'hr': {
                    'regex': 'H&R.*?(\\d+)',
                    'handle': self.handle_hr
                }

            }
        })
        return selector

    def handle_hr(self, hr):
        return str(100 - int(hr))

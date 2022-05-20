from ..schema.nexusphp import VisitHR
from ..utils import net_utils


class MainClass(VisitHR):
    URL = 'https://tjupt.org/'
    USER_CLASSES = {
        'uploaded': [5368709120000, 53687091200000],
        'days': [336, 924]
    }

    def build_selector(self):
        selector = super(VisitHR, self).build_selector()
        net_utils.dict_merge(selector, {
            'details': {
                'downloaded': None,
                'share_ratio': None,
                'seeding': {
                    'regex': '活动种子.*?(\\d+)'
                },
                'leeching': {
                    'regex': '活动种子.*?\\d+\\D+(\\d+)'
                },
                'hr': {
                    'regex': 'H&R.*?(\\d+)',
                    'handle': self.handle_hr
                }

            }
        })
        return selector

    def handle_hr(self, hr):
        return str(100 - int(hr))

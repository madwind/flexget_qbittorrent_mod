from ..utils.net_utils import dict_merge
from ..schema.nexusphp import Attendance


class MainClass(Attendance):
    URL = 'https://www.3wmg.com/)'
    USER_CLASSES = {
        'downloaded': [1099511627776, 16492674416640],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'do_not_strip': True
                }
            },
            'details': {
                'share_ratio': {
                    'regex': '分享率：(無限|[\\d.]+)',
                },
            }
        })
        return selector

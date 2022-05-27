from typing import Final

from ..schema.nexusphp import Attendance
from ..utils.net_utils import dict_merge


class MainClass(Attendance):
    URL: Final = 'https://gainbound.net/'
    USER_CLASSES: Final = {
        'uploaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'points': [400000, 1000000],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        dict_merge(selector, {
            'details': {
                'points': {
                    'regex': r'做种积分: ([\d.]+)'
                }
            }
        })
        return selector

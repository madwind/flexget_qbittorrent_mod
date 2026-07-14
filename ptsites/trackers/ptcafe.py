from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://ptcafe.club/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'points': [400000, 1000000],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': r'做种积分.*?([\d,.]+)'
                },
            }
        })
        return selector

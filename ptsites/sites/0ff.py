from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://pt.0ff.cc/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(3, 'TiB')],
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

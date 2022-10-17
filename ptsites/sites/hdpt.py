from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://hdpt.xyz/'
    USER_CLASSES: Final = {
        'downloaded': [size(1000, 'GiB'), size(3, 'TiB')],
        'share_ratio': [6, 9],
        'points': [500000, 1200000],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': (r'(做种积分).*?([\d,.]+)', 2)
                },
            }
        })
        return selector

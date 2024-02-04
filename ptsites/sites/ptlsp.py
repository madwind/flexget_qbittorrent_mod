from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://www.ptlsp.com/'
    USER_CLASSES: Final = {
        'downloaded': [size(1000, 'GiB'), size(3000, 'GiB')],
        'share_ratio': [6, 9],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': r'莉莉.*?([\d,.]+)'
                }
            }
        })
        return selector

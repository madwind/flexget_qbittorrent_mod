from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://hdvideo.one/'
    USER_CLASSES: Final = {
        'downloaded': [size(2, 'TiB'), size(8, 'TiB')],
        'share_ratio': [4, 5.5],
        'points': [423360, 934752],
        'days': [24 * 7, 52 * 7]
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

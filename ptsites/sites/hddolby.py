from typing import Final

from ..base.reseed import ReseedCookie
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(AttendanceHR, ReseedCookie):
    URL: Final = 'https://www.hddolby.com/'
    USER_CLASSES: Final = {
        'downloaded': [size(2,'TiB'), size(8,'TiB')],
        'share_ratio': [4.5, 5.5],
        'points': [470400, 1128960],
        'days': [140, 336]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': '做种积分.*?([\\d,.]+)'
                }
            }
        })
        return selector

from typing import Final

from ..base.reseed import ReseedCookie
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(AttendanceHR, ReseedCookie):
    URL: Final = 'https://www.pthome.net/'
    USER_CLASSES: Final = {
        'downloaded': [size(2, 'TiB'), size(6, 'TiB')],
        'share_ratio': [1.5, 1.8],
        'points': [600000, 1200000],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(1)',
                    }
                }
            },
            'details': {
                'points': {
                    'regex': '做种积分([\\d.,]+)',
                }
            }
        })
        return selector

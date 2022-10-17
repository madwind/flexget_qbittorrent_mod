from typing import Final

from ..base.reseed import ReseedCookie
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils


class MainClass(AttendanceHR, ReseedCookie):
    URL: Final = 'https://www.pthome.net/'
    USER_CLASSES: Final = {
        'downloaded': [1073741824000, 3221225472000],
        'share_ratio': [6, 9],
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

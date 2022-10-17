from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://springsunday.net/'
    USER_CLASSES: Final = {
        'uploaded': [1832519379627, 109951162777600],
        'downloaded': [2199023255552, 10995116277760],
        'share_ratio': [1.2, 2],
        'points': [400000, 2000000],
        'days': [35, 35]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > div:nth-child(1) > span',
                    }
                }
            },
            'details': {
                'points': {
                    'regex': '做种积分: ([\\d.,]+)',
                }
            }
        })
        return selector

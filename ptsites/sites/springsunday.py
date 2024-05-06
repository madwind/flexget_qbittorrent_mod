from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://springsunday.net/'
    USER_CLASSES: Final = {
        'downloaded': [size(2, 'TiB'), size(11.5, 'TiB')],
        'share_ratio': [1.2, 2],
        'points': [400000, 2300000],
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': '#info_block > div:nth-child(1) > span',
                        'table': '#outer div.main:last-child'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': r'做种积分.*?([\d.,]+)',
                }
            }
        })
        return selector

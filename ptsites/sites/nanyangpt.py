from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://nanyangpt.com/'
    SUCCEED_REGEX: Final = '魔力豆 \\(.*?\\)'
    USER_CLASSES: Final = {
        'downloaded': [536870912000, 1099511627776],
        'share_ratio': [5.5, 8.5],
        'days': [140, 350]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#userlink > ul > div:nth-child(3)'
                    }
                }
            }
        })
        return selector

from typing import Final

from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance):
    URL: Final = 'https://ultrahd.net/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [5, 6.5],
        'days': [175, 280]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'table': '#outer > font > table:last-of-type',
                    }
                }
            }
        })
        return selector

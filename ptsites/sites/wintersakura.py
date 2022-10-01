from typing import Final

from ..schema.nexusphp import Attendance
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(Attendance):
    URL: Final = 'https://wintersakura.net/'
    USER_CLASSES: Final = {
        'downloaded': [size(10, 'TiB')],
        'share_ratio': [9.5],
        'points': [2800000],
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'link': None,
                    'elements': {
                        'table': None,
                    }
                }
            },
            'details': {
                'join_date': None,
                'points': {
                    'regex': (r'(做种积分).*?([\d,.]+)', 2)
                },
            }
        })
        return selector

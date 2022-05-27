from typing import Final

from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance):
    URL: Final = 'https://lemonhd.org/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [175, 364]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block'
                    }
                }
            },
            'details': {
                'seeding': {
                    'regex': '做种数.*?(\\d+)'
                },
                'leeching': {
                    'regex': '下载数.*?(\\d+)'
                }
            }
        })
        return selector

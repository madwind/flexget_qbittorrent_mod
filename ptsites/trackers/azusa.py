from typing import Final

from ..schema.nexusphp import Attendance
from ..utils.net_utils import dict_merge


class MainClass(Attendance):
    URL: Final = 'https://azusa.wiki/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        dict_merge(selector, {
            'details': {
                'seeding': {
                    'regex': (r'[清理].*?\d+.*?(\d+)', 1)
                },
                'leeching': {
                    'regex': (r'[清理].*?\d+.*?(\d+).*?(\d+)', 2)
                },
            }
        })
        return selector
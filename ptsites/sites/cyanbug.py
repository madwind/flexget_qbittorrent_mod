from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://cyanbug.net/'
    USER_CLASSES: Final = {
        'downloaded': [805_306_368_000, 3_298_534_883_328],
        'share_ratio': [3.05, 4.55],
        'points': [400000, 1000000],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block .medium > div'
                    }
                }
            },
            'details': {
                'seeding': {
                    'regex': r'当前做种.*?(\d+)'
                },
                'leeching': {
                    'regex': r'当前下载.*?(\d+)'
                },
                'points': {
                    'regex': r'做种积分([\d.,]+)',
                }
            }
        })
        return selector

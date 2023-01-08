from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils.net_utils import dict_merge, get_module_name


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://gainbound.net/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'points': [400000, 1000000],
        'days': [280, 700]
    }

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        dict_merge(selector, {
            'details': {
                'points': {
                    'regex': r'做种积分([\d,.]+)'
                }
            }
        })
        return selector

from typing import Final

from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(AttendanceHR):
    URL: Final = 'https://www.pthome.net/'
    USER_CLASSES: Final = {
        'downloaded': [1073741824000, 3221225472000],
        'share_ratio': [6, 9],
        'points': [600000, 1200000],
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

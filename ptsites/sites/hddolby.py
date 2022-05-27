from typing import Final

from ..schema.nexusphp import AttendanceHR
from ..utils.net_utils import get_module_name


class MainClass(AttendanceHR):
    URL: Final = 'https://www.hddolby.com/'
    USER_CLASSES: Final = {
        'downloaded': [1099511627776, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [112, 336]
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

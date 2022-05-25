from ..utils.net_utils import get_module_name
from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL = 'https://www.hddolby.com/'
    USER_CLASSES = {
        'downloaded': [1099511627776, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [112, 336]
    }

    @classmethod
    def reseed_build_schema(cls):
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils


class MainClass(AttendanceHR):
    URL = 'https://www.pthome.net/'
    USER_CLASSES = {
        'downloaded': [1073741824000, 3221225472000],
        'share_ratio': [6, 9],
        'points': [600000, 1200000],
        'days': [280, 700]
    }

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
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

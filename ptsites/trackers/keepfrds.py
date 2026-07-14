from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://pt.keepfrds.com/'
    USER_CLASSES: Final = {
        'downloaded': [1099511627776, 4398046511104],
        'share_ratio': [3.5, 5],
        'points': [640000, 2560000],
        'days': [420, 1050]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(1)'
                    }
                }
            },
            'details': {
                'seeding': {
                    'regex': (r'下载量.*?\|.*?(\d+)', 1)
                },
                'leeching': {
                    'regex': (r'下载量.*?\|.*?(\d+).*?(\d+)', 2)
                },

            }
        })
        return selector

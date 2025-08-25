from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://ptsbao.club/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [112, 364]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'uploaded': {
                    'regex': r'上传量:  ([\d,.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': r'下载量:  ([\d,.]+ [ZEPTGMK]?B)'
                },
                'points': {
                    'regex': '魔力值.*?：([\\d,.]+)'
                }
            }
        })
        return selector

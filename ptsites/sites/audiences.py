from __future__ import annotations

from typing import Final

from ..base.reseed import ReseedCookie
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils


class MainClass(AttendanceHR, ReseedCookie):
    URL: Final = 'https://audiences.me/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4.5, 5],
        'days': [560, 784]
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

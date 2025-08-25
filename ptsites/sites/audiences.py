from __future__ import annotations

from typing import Final
from urllib.parse import urljoin

from ..base.entry import SignInEntry
from ..base.reseed import ReseedCookie
from ..base.work import Work
from ..schema.nexusphp import VisitHR
from ..utils import net_utils


class MainClass(VisitHR, ReseedCookie):
    URL: Final = 'https://audiences.me/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4.5, 5],
        'points': [1200000, 1800000],
        'days': [560, 784]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        entry['extra_msg'] = f' 未签到: {urljoin(self.URL, "/attendance_new.php")}'
        return super().sign_in_build_workflow(entry, config)

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

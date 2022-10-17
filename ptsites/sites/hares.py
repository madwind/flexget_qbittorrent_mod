from __future__ import annotations

from typing import Final

from requests import Response

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_sign_in_state, check_final_state, SignState
from ..base.work import Work
from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://club.hares.top/'
    USER_CLASSES: Final = {
        'downloaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [364]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['已签到'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/attendance.php?action=sign',
                method=self.sign_in_by_punch_in,
                succeed_regex=[
                    '签到成功',
                    '您今天已经签到过了'
                ],
                assert_state=(check_final_state, SignState.SUCCEED),
            ),
        ]

    def sign_in_by_punch_in(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        return self.request(entry, 'get', work.url, headers={'accept': 'application/json'})

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'bar': 'ul.list-inline',
                        'table': 'div.layui-col-md10 > table:nth-child(1) > tbody'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': '奶糖.(?:>.*?){4}([\\d,.]+)',
                    'handle': self.handle_points
                },
                'seeding': {
                    'regex': ('(做种中).*?(\\d+)', 2)
                },
                'leeching': {
                    'regex': ('(下载中).*?\\d+\\D+(\\d+)', 2)
                },
                'hr': None
            }
        })
        return selector

    def handle_points(self, value: str) -> str:
        return '0' if value in ['.'] else value

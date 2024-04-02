from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://www.pttime.org/'
    USER_CLASSES: Final = {
        'downloaded': [3221225472000, 16106127360000],
        'share_ratio': [3.05, 4.55],
        'days': [112, 364]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=[
                    '这是你的第.*?次签到，已连续签到.*天，本次签到获得.*个魔力值。',
                    '获得魔力值：\\d+',
                    '今天已签到，请勿重复刷新'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block',
                    }
                },
            },
            'details': {
                'seeding': {
                    'regex': r'活动:.*?(\d+)'
                },
                'leeching': {
                    'regex': (r'活动:.*?(\d+).*?(\d+)', 2)
                },
            }
        })
        return selector

    def get_nexusphp_messages(self, entry: SignInEntry, config: dict, **kwargs) -> None:
        super().get_nexusphp_messages(entry, config, unread_elements_selector='td > i[alt*="Unread"]')

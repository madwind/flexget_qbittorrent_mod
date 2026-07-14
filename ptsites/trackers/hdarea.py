from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_sign_in_state, SignState, check_final_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://hdarea.club/'
    USER_CLASSES: Final = {
        'downloaded': [1099511627776, 10995116277760],
        'share_ratio': [4.5, 6],
        'days': [140, 280]
    }

    DATA = {
        'fixed': {
            'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
            'signed_token': '(?<=signed_token: ").*(?=")'
        }
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[
                    '<span id="sign_in_done"><font color="green">\\[已签到\\]</font></></font>&nbsp;\\(\\d+\\)'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/sign_in.php?action=sign_in',
                method=self.sign_in_by_post,
                data=self.DATA,
                succeed_regex=['已连续签到.*天，此次签到您获得了.*魔力值奖励!|请不要重复签到哦！'],
                assert_state=(check_final_state, SignState.SUCCEED)
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'table': '#outer table.main'
                    }
                }
            },
            'details': {
                'hr': None
            }
        })
        return selector

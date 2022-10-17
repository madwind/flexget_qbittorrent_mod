from typing import Final

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_sign_in_state, SignState, check_final_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://pt.hd4fans.org/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    DATA = {
        'fixed': {
            'action': 'checkin'
        }
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<span id="checkedin">\\[签到成功\\]</span>'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/checkin.php',
                method=self.sign_in_by_post,
                data=self.DATA,
                assert_state=(check_network_state, NetworkState.SUCCEED)
            ),
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<span id="checkedin">\\[签到成功\\]</span>'],
                assert_state=(check_final_state, SignState.SUCCEED)
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

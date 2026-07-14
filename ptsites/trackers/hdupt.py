from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://pt.hdupt.com/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [5.59, 8.85],
        'days': [280, 700]
    }
    DATA = {
        'fixed': {
            'action': (None, 'qiandao')
        }
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<span id="yiqiandao">\\[已签到\\]</span>'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/added.php',
                method=self.sign_in_by_post,
                data=self.DATA,
                succeed_regex=['\\d+'],
                assert_state=(check_final_state, SignState.SUCCEED),
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

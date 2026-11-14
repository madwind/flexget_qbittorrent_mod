from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import SignState, check_final_state, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL: Final = 'https://www.htpt.cc/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        succeed_regex = [r'今日已签到']
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=succeed_regex,
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/attendance.php',
                method=self.sign_in_by_post,
                data={'fixed': {'action': 'sign'}},
                succeed_regex=succeed_regex,
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
            ),
        ]

from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.nexusphp import Visit


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://byr.pt/'
    USER_CLASSES: Final = {
        'uploaded': [4398046511104, 140737488355328],
        'share_ratio': [3.05, 4.55],
        'days': [168, 336]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/index.php',
                method=self.sign_in_by_get,
                succeed_regex=['欢迎'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

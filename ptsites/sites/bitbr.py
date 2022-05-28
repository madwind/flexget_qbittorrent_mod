import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.nexusphp import Attendance


class MainClass(Attendance):
    URL: Final = 'https://bitbr.cc/'
    USER_CLASSES: Final = {
        'downloaded': [805_306_368_000, 3_298_534_883_328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=[
                    rf'{re.escape("Você já resgatou ")}.*?{re.escape(" dias. Com isso, coletou ")}.*?{re.escape(" dia(s) consecutivos e dessa vez você receberá um bônus de ")}.*?{re.escape(".")}'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

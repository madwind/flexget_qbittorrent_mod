import re

from ..base.base import SignState, Work
from ..schema.nexusphp import Attendance


class MainClass(Attendance):
    URL = 'https://bitbr.cc/'
    USER_CLASSES = {
        'downloaded': [805_306_368_000, 3_298_534_883_328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/attendance.php',
                method='get',
                succeed_regex=[
                    rf'{re.escape("Você já resgatou ")}.*?{re.escape(" dias. Com isso, coletou ")}.*?{re.escape(" dia(s) consecutivos e dessa vez você receberá um bônus de ")}.*?{re.escape(".")}'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

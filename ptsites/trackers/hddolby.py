from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedCookie
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(AttendanceHR, ReseedCookie):
    URL: Final = 'https://www.hddolby.com/'
    USER_CLASSES: Final = {
        'downloaded': [size(2, 'TiB'), size(8, 'TiB')],
        'share_ratio': [4.5, 5.5],
        'points': [720000, 1680000],
        'days': [194, 392]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=[
                    '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*个鲸币。',
                    '签到已得\\d+',
                    '您今天已经签到过了，请勿重复刷新。|您今天已經簽到過了，請勿重複刷新。'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': r'做种积分.*?([\d,.]+)'
                }
            }
        })
        return selector

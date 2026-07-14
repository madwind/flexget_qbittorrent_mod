from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://pterclub.net/'
    IGNORE_TITLE = '认领种子获得猫粮60000克'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [210, 315]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['签到已得\\d+'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/attendance-ajax.php',
                method=self.sign_in_by_get,
                succeed_regex=[
                    '这是您的第 .* 次签到，已连续签到 .* 天。.*本次签到获得 .* 克猫粮。',
                    '签到已得\\d+',
                    '您今天已经签到过了，请勿重复刷新。'
                ],
                assert_state=(check_final_state, SignState.SUCCEED),
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
                'points': {
                    'regex': '猫粮.*?([\\d,.]+)'
                }
            }
        })
        return selector

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config, ignore_title=self.IGNORE_TITLE)

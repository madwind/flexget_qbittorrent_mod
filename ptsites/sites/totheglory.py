from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP):
    URL: Final = 'https://totheglory.im/'
    USER_CLASSES: Final = {
        'uploaded': [769658139444, 109951162777600],
        'downloaded': [3848290697216, 10995116277760],
        'share_ratio': [5, 6],
        'days': [224, 336]
    }

    DATA = {
        'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
        'signed_token': '(?<=signed_token: ").*(?=")'
    }

    def sign_in(self, entry: SignInEntry, config: dict) -> None:
        entry.fail_with_prefix("公告禁止使用脚本，请移除")
        return

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<b style="color:green;">已签到</b>'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/signed.php',
                method=self.sign_in_by_post,
                data=self.DATA,
                succeed_regex=['您已连续签到\\d+天，奖励\\d+积分，明天继续签到将获得\\d+积分奖励。'],
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
                        'bar': 'body > table:nth-child(3) > tbody > tr > td > table > tbody > tr > td:nth-child(1)',
                        'table': '#main_table > tbody > tr:nth-child(1) > td > table > tbody > tr > td > table > tbody'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': ('(上[传傳]量|Uploaded).+?([\\d.]+ ?[ZEPTGMk]?i?B)', 2),
                    'handle': self.handle_size
                },
                'downloaded': {
                    'regex': ('(下[载載]量|Downloaded).+?([\\d.]+ ?[ZEPTGMk]?i?B)', 2),
                    'handle': self.handle_size
                },
                'points': {
                    'regex': '积分.*?([\\d,.]+)'
                },
                'seeding': {
                    'regex': '做种活动.*?(\\d+)'
                },
                'leeching': {
                    'regex': '做种活动.*?\\d+\\D+(\\d+)'
                },
                'hr': {
                    'regex': 'HP.*?(\\d+)',
                    'handle': self.handle_hr
                }
            }
        })
        return selector

    def handle_size(self, size: str) -> str:
        return size.upper()

    def handle_hr(self, hr: str) -> str:
        return str(15 - int(hr))

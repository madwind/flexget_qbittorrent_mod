from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import SignState, check_final_state
from ..base.work import Work
from ..schema.nexusphp import VisitHR
from ..utils.value_handler import size, handle_infinite


class MainClass(VisitHR, ReseedPasskey):
    URL: Final = 'https://hhanclub.net/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(3, 'TiB')],
        'points': [900000, 1500000],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }
    @property
    def SUCCEED_REGEX(self) -> str:
        return 'HHCLUB :: 首页'

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        # 主动签到领憨豆（原版此段被注释；这里启用并补上「今日已签到」兜底，
        # 以免一天内跑第二次因匹配不到成功文案而被判失败）。
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=[
                    r'这是您的第[\d,]+次[签簽]到，已[连連][续續][签簽]到[\d,]+天，本次[签簽]到[获獲]得[\d,]+个憨豆',
                    r'[签簽]到已得\d+',
                    r'今天已.*?[签簽]到|您今天已[经經][签簽]到过了|请勿重复',
                ],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'userdetails\.php\?id=(\d+)',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'panel': '#user-info-panel',
                        'table': '#mainContent'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'上传量.+?([\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'downloaded': {
                    'regex': r'下载量.+?([\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': {
                    'regex': r'分享率.*?(---|∞|Inf\.|无限|無限|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'做种积分：.*?([\d,.]+)'
                },
                'join_date': {
                    'regex': r'加入日期.*?(\d{4}-\d{2}-\d{2})',
                },
                'seeding': {
                    'regex': (r'勋章.*?([\d,.]+).*?([\d,.]+)', 2)
                },
                'leeching': {
                    'regex': (r'勋章.*?([\d,.]+).*?([\d,.]+).*?([\d,.]+).*?([\d,.]+)', 4)
                },
                'hr': {
                    'regex': r'H&R.*?(\d+)'
                }
            }
        }

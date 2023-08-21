from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.nexusphp import AttendanceHR
from ..utils.value_handler import size, handle_infinite


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://hhanclub.top/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(3, 'TiB')],
        'points': [900000, 1500000],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

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

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=[r'这是您的第\d+次签到，已连续签到\d+天，本次签到获得\d+个憨豆。'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

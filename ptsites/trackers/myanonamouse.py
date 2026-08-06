from __future__ import annotations

from typing import Final

from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.value_handler import handle_join_date, handle_infinite


class MainClass(PrivateTorrent):
    URL: Final = 'https://www.myanonamouse.net/'
    USER_CLASSES: Final = {
        'uploaded': [26843545600],
        'share_ratio': [2.0],
        'days': [28]
    }

    # 不再重写 sign_in_build_schema —— 基类默认就是 cookie 字符串模式
    # 配置写法:
    #   sign_in:
    #     sites:
    #       myanonamouse: 'mam_id=xxxxxxxx...'

    def sign_in_build_workflow(self, entry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['Log Out'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': '/u/(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/u/{}',
                    'elements': {
                        'bar': '.mmUserStats ul',
                        'table': 'table.coltable'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded\s+([\d.,]+ [ZEPTGMK]i?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded\s+([\d.,]+ [ZEPTGMK]i?B)'
                },
                'share_ratio': {
                    'regex': r'Share\s*ratio\s*?(∞|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'Bonus:\s+([\d,.]+)'
                },
                'join_date': {
                    'regex': r'Join\s+date\s+(\d{4}-\d{2}-\d{2})',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': r'(\d+)\s+seeding\s+unsatisfied\s+torrents'
                },
                'leeching': {
                    'regex': r'(\d+)\s+leeching\s+torrents'
                },
                'hr': None
            }
        }

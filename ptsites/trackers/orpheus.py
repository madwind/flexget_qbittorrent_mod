from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Final

from ..base.entry import SignInEntry
from ..base.request import NetworkState, check_network_state
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.net_utils import get_module_name
from ..utils.value_handler import handle_infinite


def parse_relative_date(text: str) -> str:
    """
    一个辅助函数，用于将 "X years, Y months ago" 这样的相对日期
    转换成 'YYYY-MM-DD' 格式的近似绝对日期。
    """
    try:
        today = datetime.now()
        total_days = 0
        
        years_match = re.search(r'(\d+)\s*years?', text)
        if years_match:
            total_days += int(years_match.group(1)) * 365

        months_match = re.search(r'(\d+)\s*months?', text)
        if months_match:
            total_days += int(months_match.group(1)) * 30
        
        weeks_match = re.search(r'(\d+)\s*weeks?', text)
        if weeks_match:
            total_days += int(weeks_match.group(1)) * 7
            
        days_match = re.search(r'(\d+)\s*days?', text)
        if days_match:
            total_days += int(days_match.group(1))
            
        if total_days > 0:
            join_date = today - timedelta(days=total_days)
            return join_date.strftime('%Y-%m-%d')
    except Exception:
        pass
    
    return '1970-01-01'


class MainClass(Gazelle):
    URL: Final = 'https://orpheus.network/'
    USER_CLASSES: Final = {
        'uploaded': [26843545600, 2199023255552],
        'share_ratio': [1.05, 1.05],
        'days': [14, 56]
    }

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'},
                    'login': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string'},
                            'password': {'type': 'string'}
                        },
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
            'mfa': '',
            'keeplogged': 1,
            'login': 'Log in',
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login.php',
                method=self.sign_in_by_login,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                response_urls=['/index.php'],
            ),
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<h1 class="site_name">Orpheus</h1>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#userinfo_stats',
                        'table': 'div.sidebar'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'(?:Up|Uploaded):\s*([\d.]+\s*[ZEPTGMK]?i?B)'
                },
                'downloaded': {
                    'regex': r'(?:Down|Downloaded):\s*([\d.]+\s*[ZEPTGMK]?i?B)'
                },
                'share_ratio': {
                    'regex': r'Ratio:\s*(∞|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'Bonus Points:\s*([\d,]+)'
                },
                'seeding': {
                    'regex': r'Seeding:\s*(\d+)'
                },
                'leeching': {
                    'regex': r'Leeching:\s*(\d+)'
                },
                # 最终修复：抓取相对日期并交由我们新增的函数处理
                'join_date': {
                    'regex': r'Joined:\s*(.+? ago)',
                    'handle': parse_relative_date
                }
            }
        })
        return selector

import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.net_utils import get_module_name
from ..utils.value_hanlder import handle_infinite


class MainClass(PrivateTorrent):
    URL: Final = 'https://speedapp.io/'
    USER_CLASSES: Final = {
        'uploaded': [109951162777600],
        'share_ratio': [6],
        'days': [2190],
    }

    @classmethod
    def sign_in_build_schema(cls):
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
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
            '_csrf_token': re.search(r'(?<=name="_csrf_token" value=").+?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            '_remember_me': 'on',
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/zh/%E7%99%BB%E5%BD%95?locale=zh',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/zh/登录?locale=zh',
                method=self.sign_in_by_login,
                succeed_regex=['logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'detail_sources': {
                'menu-stats': {
                    'do_not_strip': True,
                    'link': '/profile/menu-stats',
                    'elements': {
                        'all': 'body',
                    }
                },
                'profile': {
                    'link': '/profile',
                    'elements': {
                        'table': '#kt_content > div.d-flex.flex-column-fluid > div > div > div.flex-row-fluid.ml-lg-8'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'''(?x)已上传
                                    \s*
                                    ([\d.] + \ [ZEPTGMK] ? B)''',
                },
                'downloaded': {
                    'regex': r'''(?x)已下载
                                    \s*
                                    ([\d.] + \ [ZEPTGMK] ? B)''',
                },
                'share_ratio': {
                    'regex': r'''(?x)比率">
                                    \s*
                                    <i\ class="fas\ fa-fw\ fa-chart-line\ text-info\ fa-sm"></i>
                                    \s*
                                    (Inf. | [\d,.] +)''',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'''(?x)奖励积分">
                                    \s*
                                    <i\ class="fas\ fa-fw\ fa-coins\ text-warning\ fa-sm"></i>
                                    \s*
                                    ([\d,.] +)'''
                },
                'join_date': {
                    'regex': r'''(?x)注册日期
                                    \s*
                                    (\d + 年 \d + 月 \d + 日)''',
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': r'''(?x)目前正在播种种子">
                                    \s*
                                    <i\ class="far\ fa-fw\ fa-arrow-alt-circle-up\ text-muted\ fa-sm"></i>
                                    \s*
                                    ([\d,] +)'''
                },
                'leeching': {
                    'regex': r'''(?x)目前正在窃取种子">
                                    \s*
                                    <i\ class="far\ fa-fw\ fa-arrow-alt-circle-down\ text-danger\ text-muted\ fa-sm"></i>
                                    \s*
                                    ([\d,] +)'''
                },
                'hr': {
                    'regex': r'''(?x)HnR
                                    \ 
                                    ([\d,] +)'''
                }
            }
        }

    def handle_join_date(self, value: str) -> str:
        return value.translate(str.maketrans('年月', '--', '日'))

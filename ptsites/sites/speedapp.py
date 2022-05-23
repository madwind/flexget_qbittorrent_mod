import re

from ..schema.site_base import SiteBase, Work, SignState, NetworkState
from ..utils.value_hanlder import handle_infinite


class MainClass(SiteBase):
    URL = 'https://speedapp.io/'
    USER_CLASSES = {
        'uploaded': [109951162777600],
        'share_ratio': [6],
        'days': [2190],
    }

    @classmethod
    def build_sign_in_schema(cls):
        return {
            cls.get_module_name(): {
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

    def build_login_workflow(self, entry, config):
        return [
            Work(
                url='/zh/%E7%99%BB%E5%BD%95?locale=zh',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/zh/登录?locale=zh',
                method='login',
                succeed_regex=['logout'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
            )
        ]

    def build_login_data(self, login, last_content):
        return {
            '_csrf_token': re.search(r'(?<=name="_csrf_token" value=").+?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            '_remember_me': 'on',
        }

    def build_selector(self):
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

    def handle_join_date(self, value):
        return value.translate(str.maketrans('年月', '--', '日'))

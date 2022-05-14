import re

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_join_date(value):
    return value.translate(str.maketrans('年月', '--', '日'))


def handle_share_ratio(value):
    if value == 'Inf.':
        return '0'
    else:
        return value


def build_selector():
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
                'handle': handle_share_ratio
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
                'handle': handle_join_date
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
                method='password',
                succeed_regex='logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
                token_regex=r'''(?x)(?<= name="_csrf_token"\ value=")
                                    . +?
                                    (?= ")''',
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            '_csrf_token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            '_remember_me': 'on',
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

    def get_message(self, entry, config):
        entry['result'] += '(TODO: Message)'  # TODO: Feature not implemented yet

    def get_details(self, entry, config):
        self.get_details_base(entry, config, build_selector())

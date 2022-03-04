from ..schema.nexusphp import Attendance
from ..schema.site_base import Work, SignState
from ..utils.net_utils import NetUtils


class MainClass(Attendance):
    URL = 'https://club.hares.top/'
    USER_CLASSES = {
        'downloaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [364]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/attendance.php',
                method='get',
                succeed_regex=[
                    '这是您的第 \\d+ 次签到，已连续签到 \\d+ 天，本次签到获得 \\d+ 个奶糖。',
                    '已签到'
                ],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'bar': 'ul.list-inline',
                        'table': 'div.layui-col-md10 > table:nth-child(1) > tbody'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': '奶糖.*?([\\d,.]+)',
                    'handle': self.handle_points
                },
                'seeding': {
                    'regex': ('(做种中).*?(\\d+)', 2)
                },
                'leeching': {
                    'regex': ('(下载中).*?\\d+\\D+(\\d+)', 2)
                },
                'hr': None
            }
        })
        return selector

    def handle_points(self, value):
        if value in ['.']:
            return '0'
        else:
            return value

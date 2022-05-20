from ..schema.nexusphp import Attendance
from ..schema.site_base import Work, SignState
from ..utils import net_utils


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
                url='/',
                method='get',
                succeed_regex='已签到',
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/attendance.php?action=sign',
                method='punch_in',
                succeed_regex=[
                    '签到成功',
                    '您今天已经签到过了'
                ],
                check_state=('final', SignState.SUCCEED),
            ),
        ]

    def sign_in_by_punch_in(self, entry, config, work, last_content):
        return self._request(entry, 'get', work.url, headers={'accept': 'application/json'})

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
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
                    'regex': '奶糖.(?:>.*?){4}([\\d,.]+)',
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

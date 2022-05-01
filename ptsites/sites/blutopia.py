from ..schema.site_base import SignState, Work
from ..schema.unit3d import Unit3D
from ..utils.net_utils import NetUtils


class MainClass(Unit3D):
    URL = 'https://blutopia.xyz/'
    USER_CLASSES = {
        'uploaded': [109951162777600],
        'days': [365]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<title>Blutopia - Where Quality Matters</title>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'user_id': '/users/(.*?)/',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': 'ul.top-nav__ratio-bar',
                        'header': '.header',
                        'data_table': '.user-info'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': 'title="My Bonus Points".*?</i>.+?(\\d[\\d,. ]*)',
                },
                'share_ratio': {
                    'regex': 'title="Ratio".*?</i>.+?(\\d[\\d,. ]*)',
                },
                'join_date': {
                    'regex': 'Registration date (.*?\\d{4})',
                    'handle': self.handle_join_date
                },
                'hr': {
                    'regex': 'Active Warnings.+?(\\d+)'
                }
            }
        })
        return selector

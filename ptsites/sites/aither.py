from flexget.entry import Entry

from ..schema.site_base import SignState, Work
from ..schema.unit3d import Unit3D
from ..utils import net_utils
from ..utils.value_hanlder import handle_join_date


class MainClass(Unit3D):
    URL: str = 'https://aither.cc/'
    USER_CLASSES: dict = {
        'uploaded': [43980465111040],
        'days': [365]
    }

    def build_workflow(self, entry: Entry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<title>Aither - Heaven</title>',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self) -> dict:
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
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
                    'handle': handle_join_date
                },
                'hr': {
                    'regex': 'Active Warnings.+?(\\d+)'
                }
            }
        })
        return selector

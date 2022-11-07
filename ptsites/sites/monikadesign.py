from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.unit3d import Unit3D
from ..utils import net_utils
from ..utils.value_handler import handle_join_date, size


class MainClass(Unit3D):
    URL: Final = 'https://monikadesign.uk/'
    USER_CLASSES: Final = {
        'uploaded': [size(15, 'TiB')],
        'days': [36500]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[(r'<a href="https://monikadesign.uk/users/(.*?)">个人资料</a>', 1)],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'user_id': '/users/(.*)/',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': '.top-nav__stats',
                        'ratio_bar': '.top-nav__ratio-bar',
                        'header': '.header',
                        'data_table': '.user-info'
                    }
                }
            },
            'details': {
                'leeching': {
                    'regex': (r'(下载).+?(\d+)', 2)
                },
                'points': {
                    'regex': 'title="我的魔力".*?</i>.+?(\\d[\\d,. ]*)',
                },
                'share_ratio': {
                    'regex': 'title="分享率".*?</i>.+?(\\d[\\d,. ]*)',
                },
                'join_date': {
                    'regex': '注册日期 (.*?\\d{4})',
                    'handle': handle_join_date
                },
                'hr': None
            }
        })
        return selector

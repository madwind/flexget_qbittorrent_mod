from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.unit3d import Unit3D
from ..utils import net_utils
from ..utils.value_handler import handle_join_date


class MainClass(Unit3D):
    URL: Final = 'https://aither.cc/'
    USER_CLASSES: Final = {
        'uploaded': [43980465111040],
        'days': [365]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<title>Aither - Heaven</title>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'user_id': '/users/(.*?)/',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': 'ul.top-nav__ratio-bar',
                        'registration_date': 'article > time',
                        'warnings': 'article > aside > section:nth-child(2)',
                        'data_table': 'article > aside > section:nth-child(4)'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Upload.+?([\d.]+.?[ZEPTGMK]?iB)',
                    'handle': self.remove_symbol
                },
                'downloaded': {
                    'regex': r'Download.+?([\d.]+.?[ZEPTGMK]?iB)',
                    'handle': self.remove_symbol
                },
                'points': {
                    'regex': r'title="My bonus points".*?</i>.*?(\d[\d,. ]*)',
                },
                'share_ratio': {
                    'regex': 'title="Ratio".*?</i>.+?(\\d[\\d,. ]*)',
                },
                'join_date': {
                    'regex': r'Registration date.*?(\d{4}-\d{2}-\d{2})',
                    'handle': handle_join_date
                },
                'hr': {
                    'regex': r'Hit and run count.*?(\d+)'
                }
            }
        })
        return selector

    def remove_symbol(self, value: str):
        return value.replace('\xa0', '')

import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.unit3d import Unit3D
from ..utils import net_utils
from ..utils.value_handler import handle_join_date


class MainClass(Unit3D):
    URL: Final = 'https://blutopia.cc/'
    USER_CLASSES: Final = {
        'uploaded': [109951162777600],
        'days': [365]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<title>Blutopia - Where quality matters'],
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
                        'header': 'time.profile__registration',
                        'data_table': 'article.sidebar2 aside section.panelV2:nth-of-type(2)'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'title="Upload".*?</i>.+?([\d.]+.*?[ZEPTGMK]?iB)',
                    'handle': self.handle_whitespace
                },
                'downloaded': {
                    'regex': r'title="Download".*?</i>.+?([\d.]+.*?[ZEPTGMK]?iB)',
                    'handle': self.handle_whitespace
                },
                'points': {
                    'regex': 'title="Bonus points".*?</i>.+?(\\d[\\d,.\u202f\u00a0 ]*)',
                    'handle': self.handle_number
                },
                'share_ratio': {
                    'regex': 'title="Ratio".*?</i>.+?(\\d[\\d,.\u202f\u00a0 ]*)',
                    'handle': self.handle_number
                },
                'join_date': {
                    'regex': r'Registration date:.*?(\d{4}-\d{2}-\d{2})',
                    'handle': handle_join_date
                },
                'hr': {
                    'regex': 'Active warnings.+?(\\d+)'
                }
            }
        })
        return selector

    def handle_number(self, value: str) -> str:
        # The site uses U+202F or U+00A0 as the thousands separator, which the
        # plain space class does not match. Strip them; commas are handled downstream.
        return re.sub(r'[\u202f\u00a0\s]', '', value)

    def handle_whitespace(self, value: str) -> str:
        # The gap between value and unit may be \xa0 (&nbsp;); normalise to a plain space
        return re.sub(r'\s+', ' ', value)

import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.unit3d import Unit3D
from ..utils import net_utils
from ..utils.value_handler import handle_join_date


class MainClass(Unit3D):
    URL: Final = 'https://eiga.moi/'
    USER_CLASSES: Final = {
        'downloaded': [109951162777600, 439804651110400],
        'days': [365, 730]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            # The base pattern stops at the next quote, but the first /users/
            # link on the page may carry a sub-path (e.g. /users/name/uploads),
            # which would be captured as part of the id. Stop at '/' as well.
            'user_id': r'/users/([^/"]+)',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': 'ul.top-nav__ratio-bar',
                        'registration_date': 'time.profile__registration',
                        # This skin has no .gradient element; the warnings panel
                        # is identified by its wire:name attribute instead.
                        'warnings': 'section[wire\\:name="user-warnings"]',
                        'data_table': None
                    }
                }
            },
            # The ratio bar labels follow the site language, so match on the
            # li class names instead, which are stable across locales.
            'details': {
                'uploaded': {
                    'regex': r'ratio-bar__uploaded.*?</i>\s*([\d.]+.?[ZEPTGMK]?iB)',
                    'handle': self.remove_symbol
                },
                'downloaded': {
                    'regex': r'ratio-bar__downloaded.*?</i>\s*([\d.]+.?[ZEPTGMK]?iB)',
                    'handle': self.remove_symbol
                },
                'seeding': {
                    'regex': r'ratio-bar__seeding.*?</i>\s*(\d+)'
                },
                'leeching': {
                    'regex': r'ratio-bar__leeching.*?</i>\s*(\d+)'
                },
                'points': {
                    'regex': r'ratio-bar__points.*?</i>\s*(\d[\d,.\u202f\u00a0 ]*)',
                    'handle': self.remove_symbol
                },
                'share_ratio': {
                    'regex': r'ratio-bar__ratio.*?</i>\s*(\d[\d,.]*|Inf)'
                },
                'join_date': {
                    'regex': r'profile__registration.*?(\d{4}-\d{2}-\d{2})',
                    'handle': handle_join_date
                },
                'hr': {
                    # The warnings panel has Automated / Manual / Soft deleted
                    # tabs; the first two together are the active warning count.
                    'regex': r'(Automated \(\d+\).*?Manual \(\d+\))',
                    'handle': self.sum_warnings
                }
            }
        })
        return selector

    def sum_warnings(self, value: str) -> str:
        return str(sum(int(n) for n in re.findall(r'\((\d+)\)', value)))

    def remove_symbol(self, value: str) -> str:
        return value.replace('\xa0', '').replace('\u202f', '').replace(' ', '')

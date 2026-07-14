from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils


class MainClass(Gazelle):
    URL: Final = 'https://redacted.sh/'
    USER_CLASSES: Final = {
        'uploaded': [536870912000],
        'share_ratio': [0.65],
        'days': [56]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<h1 class="hidden">Redacted</h1>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {'table': '#content > div > div.sidebar > div:nth-child(1) > ul'}
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            },
            'details': {
                'points': None,
            }
        })
        return selector

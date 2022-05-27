from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils


class MainClass(Gazelle):
    URL: Final = 'https://www.empornium.is/'
    USER_CLASSES: Final = {
        'uploaded': [107374182400],
        'share_ratio': [1.05],
        'days': [56]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<h1 class="hidden">Empornium</h1>'],
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
                    'elements': {
                        'bar': 'table.userinfo_stats',
                        'table': '#content > div > div.sidebar > div:nth-child(4) > ul',
                        'community': '#content > div > div.sidebar > div:nth-child(10) > ul'
                    }
                }
            }
        })
        return selector

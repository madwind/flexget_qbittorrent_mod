from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils


class MainClass(Gazelle):
    URL: Final = 'https://uhdbits.org/'
    USER_CLASSES: Final = {
        'downloaded': [322122547200],
        'share_ratio': [2.0],
        'days': [56]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<h1 class="hidden">UHDBits</h1>'],
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
                        'bar': 'ul#userinfo_stats',
                        'table': 'div.sidebar > div:nth-child(2) > ul'
                    }
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            }
        })
        return selector

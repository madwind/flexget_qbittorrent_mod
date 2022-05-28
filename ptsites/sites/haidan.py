from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_sign_in_state, SignState, check_final_state, Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP):
    URL: Final = 'https://www.haidan.video/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [175, 364]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/index.php',
                method=self.sign_in_by_get,
                succeed_regex=['(?<=value=")已经打卡(?=")'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/signin.php',
                method=self.sign_in_by_get,
                succeed_regex=['(?<=value=")已经打卡(?=")'],
                response_urls=['/signin.php', '/index.php'],
                assert_state=(check_final_state, SignState.SUCCEED)
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#head > div.top-panel.special-border > div > div:nth-child(2)',
                        'table': 'body > div.mainroute > div.mainpanel.special-border > table > tbody > tr > td > table'
                    }
                }
            },
            'details': {
                'hr': None
            }
        })
        return selector

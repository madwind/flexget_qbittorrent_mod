from typing import Final

from ..base.entry import SignInEntry
from ..base.request import NetworkState
from ..base.request import check_network_state
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(Gazelle):
    URL: Final = 'https://jpopsuki.eu/'
    USER_CLASSES: Final = {
        'uploaded': [26843545600],
        'share_ratio': [1.05],
        'days': [14]
    }

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'},
                    'login': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string'},
                            'password': {'type': 'string'}
                        },
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
            'keeplogged': 1,
            'login': 'Log In!',
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login.php',
                method=self.sign_in_by_login,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                response_urls=['/index.php'],
            ),
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[r'<a href="user\.php\?id=\d+" class="username">(.*?)</a>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                use_last_content=True,
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'user_id': 'user.php\\?id=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/user.php?id={}',
                    'elements': {
                        'table': '#content > div > div.sidebar > div:nth-last-child(4) > ul',
                        'Community': '#content > div > div.sidebar > div:last-child > ul'
                    }
                }
            }
        })
        return selector

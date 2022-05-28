from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.luminance import Luminance


class MainClass(Luminance):
    URL: Final = 'https://femdomcult.org/'
    USER_CLASSES: Final = {
        'downloaded': [5497558138880],
        'share_ratio': [1.05],
        'days': [56]
    }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login.php',
                method=self.sign_in_by_login,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/index.php']
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
            'keeplogged': 1,
            'login': 'Login'
        }

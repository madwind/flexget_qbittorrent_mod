import re
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
                url='/login',
                method=self.sign_in_by_get,
            ),
            Work(
                url='/login',
                method=self.sign_in_by_login,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/index.php', '/']
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        print(last_content)
        return {
            'username': login['username'],
            'password': login['password'],
            'token': re.search(r'token" value="(.*?)"', last_content).group(1),
            'cinfo': '2048|1152|24|-480',
            'submit': 'Login'
        }

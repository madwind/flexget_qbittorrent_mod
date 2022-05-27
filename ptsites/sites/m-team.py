from __future__ import annotations

import re
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils, google_auth
from ..utils.net_utils import get_module_name


class MainClass(NexusPHP):
    URL: Final = 'https://kp.m-team.cc/'
    USER_CLASSES: Final = {
        'downloaded': [2147483648000, 3221225472000],
        'share_ratio': [7, 9],
        'days': [168, 224]
    }

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'login': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string'},
                            'password': {'type': 'string'},
                            'secret_key': {'type': 'string'}
                        },
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/takelogin.php',
                method=self.sign_in_by_verify,
                succeed_regex=['歡迎回來'],
                assert_state=(check_final_state, SignState.SUCCEED),
                response_urls=['/verify.php?returnto=', '/index.php'],
                is_base_content=True,
                verify_url='/verify.php?returnto=',
            )
        ]

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
        }

    def sign_in_by_verify(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return

        login_response = self.sign_in_by_login(entry, config, work, last_content)

        login_network_state = check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        verify_url = urljoin(entry['url'], work.verify_url)
        if login_response.url.startswith(verify_url):
            content = net_utils.decode(login_response)
            attempts = re.search('您還有(\\d+)次嘗試機會，否則該IP將被禁止訪問。', content)
            if attempts:
                times = attempts.group(1)
                if times == '30':
                    google_code = google_auth.calc(login['secret_key'])
                    data = {
                        'otp': (None, google_code)
                    }
                    return self.request(entry, 'post', verify_url, files=data)
                else:
                    entry.fail_with_prefix('{} with google_auth'.format(attempts.group()))
            else:
                entry.fail_with_prefix('Attempts text not found!  with google_auth')
        return login_response

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config)
        system_message_url = '/messages.php?action=viewmailbox&box=-2'
        self.get_nexusphp_messages(entry, config, messages_url=system_message_url)

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

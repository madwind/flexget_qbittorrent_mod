from __future__ import annotations

import re
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.discuz import Discuz
from ..utils import google_auth
from ..utils.net_utils import get_module_name


class MainClass(Discuz):
    URL: Final = 'https://skyeysnow.com/'
    USER_CLASSES: Final = {
        'points': [1000000]
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
                url='/login.php',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/login.php',
                method=self.sign_in_by_login,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                login_url_regex='(?<=action=").*?(?=")',
                formhash_regex='(?<="formhash" value=").*(?=")'
            )
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<a.*?title="访问我的空间">.*?</a>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                use_last_content=True,
                is_base_content=True
            )
        ]

    def sign_in_by_login(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return None

        secret_key = login.get('secret_key')
        username, password = login['username'], login['password']

        if secret_key:
            totp_code = google_auth.calc(secret_key)
            username += '@' + totp_code

        login_url = urljoin(entry['url'], re.search(work.login_url_regex, last_content).group())
        work.response_urls = [login_url]
        formhash = re.search(work.formhash_regex, last_content).group()
        data = {
            'formhash': formhash,
            'referer': '/',
            'loginfield': 'username',
            'username': username,
            'password': password,
            'loginsubmit': 'true'
        }
        return self.request(entry, 'post', login_url, data=data, verify=False)

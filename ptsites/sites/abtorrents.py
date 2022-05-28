from __future__ import annotations

import ast
import hashlib
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.xbt import XBT


class MainClass(XBT):
    URL: Final = 'https://abtorrents.me/'
    USER_CLASSES: Final = {
        'uploaded': [536870912000],
        'share_ratio': [1.5],
        'days': [90],
    }

    def sign_in_build_login_workflow(self, entry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login.php?returnto=%2F',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/simpleCaptcha.php',
                method=self.sign_in_by_get,
                assert_state=(check_network_state, NetworkState.SUCCEED),
            ),
            Work(
                url='/takelogin.php',
                method=self.sign_in_by_login,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_by_login(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        last_content = ast.literal_eval(last_content)
        target = {'light bulb': '44c7285b', 'house': 'b9a403b9', 'musical note': '3a8441da', 'key': '2faefa2b', 'bug':
            'c2ba10a5', 'heart': 'bed5a0e2', 'clock': '99d86267', 'world': 'ededf171'}[last_content['text']]
        for hash in last_content['images']:
            if hashlib.shake_128(self.request(entry, 'get', urljoin(entry['url'], '/simpleCaptcha.php?hash=' + hash))
                                         .content).hexdigest(4) == target:
                break
        data = {
            'username': login['username'],
            'password': login['password'],
            'remember': 1,
            'captchaSelection': hash,
            'submitme': 'X',
            'returnto': '/'
        }
        return self.request(entry, 'post', work.url, data=data)

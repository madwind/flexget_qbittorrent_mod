from __future__ import annotations

import ast
import json
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(PrivateTorrent):
    URL: Final = 'https://milkie.cc/'

    @classmethod
    def sign_in_build_schema(cls):
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
                        'additionalProperties': False,
                    },
                },
                'additionalProperties': False,
            },
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/api/v1/auth/sessions',
                method=self.sign_in_by_login,
                succeed_regex=['{"token":".*"}'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/api/v1/auth/sessions'],
            )
        ]

    def sign_in_by_login(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return None
        data = {
            'email': login['username'],
            'password': login['password'],
        }
        login_response = self.request(entry, 'post', work.url, data=data)
        self.session.headers.update({'authorization': 'Bearer ' + ast.literal_eval(login_response.text)['token']})
        return login_response

    def get_details(self, entry: SignInEntry, config: dict) -> None:
        link = urljoin(entry['url'], '/api/v1/auth')
        detail_response = self.request(entry, 'get', link)
        network_state = check_network_state(entry, link, detail_response)
        if network_state != NetworkState.SUCCEED:
            return
        detail_content = net_utils.decode(detail_response)
        data = json.loads(detail_content)
        entry['details'] = {
            'uploaded': str(data['user']['uploaded']) + 'B',
            'downloaded': str(data['user']['downloaded']) + 'B',
            'share_ratio': data['user']['uploaded'] / data['user']['downloaded'] if data['user']['downloaded'] else 0,
            'points': '*',
            'join_date': data['user']['createdAt'].split('T')[0],
            'seeding': '*',
            'leeching': '*',
            'hr': '*'
        }

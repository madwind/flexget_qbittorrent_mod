from __future__ import annotations

import datetime
import json
from typing import Final
from urllib.parse import urljoin

from dateutil.parser import parse
from flexget.entry import Entry
from requests import Response, request

from ..base.entry import SignInEntry
from ..base.request import NetworkState
from ..base.reseed import Reseed
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.nexusphp import NexusPHP
from ..utils import url_recorder
from ..utils.net_utils import get_module_name
from ..utils.value_handler import handle_infinite


class MainClass(NexusPHP, Reseed):
    URL: Final = 'https://api.m-team.io/'
    PROFILE_URL = '/api/member/profile'
    MY_PEER_STATUS = '/api/tracker/myPeerStatus'
    GEN_DL_TOKEN = '/api/torrent/genDlToken'
    SUCCEED_REGEX = 'SUCCESS'
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
                    'key': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def get_details(self, entry: SignInEntry, config: dict) -> None:
        details_response_json = json.loads(entry['base_content'])
        if not details_response_json:
            return
        my_peer_status_response = self.request(entry, 'POST', urljoin(self.URL, self.MY_PEER_STATUS))
        my_peer_status_response_json = my_peer_status_response.json()
        entry['details'] = {
            'uploaded': f'{details_response_json.get("data").get("memberCount").get("uploaded") or 0} B'.replace(',',
                                                                                                                 ''),
            'downloaded': f'{details_response_json.get("data").get("memberCount").get("downloaded") or 0} B'.replace(
                ',',
                ''),
            'share_ratio': handle_infinite(
                str(details_response_json.get('data').get('memberCount').get('shareRate') or 0).replace(',', '')),
            'points': str(details_response_json.get('data').get('memberCount').get('bonus') or 0).replace(
                ',', ''),
            'seeding': str(my_peer_status_response_json.get('data').get('seeder') or 0).replace(',', ''),
            'leeching': str(my_peer_status_response_json.get('data').get('leecher') or 0).replace(',',
                                                                                                  ''),
            'hr': '*'
        }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url=self.PROFILE_URL,
                method=self.sign_in_by_post,
                data={},
                succeed_regex=[self.SUCCEED_REGEX],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def sign_in_by_post(self,
                        entry: SignInEntry,
                        config: dict,
                        work: Work,
                        last_content: str = None,
                        ) -> Response | None:
        response = super().sign_in_by_post(entry, config, work, last_content)
        response_json = response.json()
        last_browse = response_json.get('data').get('memberStatus').get('lastBrowse')
        target_date = datetime.datetime.strptime(last_browse, '%Y-%m-%d %H:%M:%S')
        days = (datetime.datetime.now() - target_date).days
        if days > 29:
            entry.fail_with_prefix(f'last browse: {days} days, {self.URL}')
            return
        return response

    def request(self,
                entry: SignInEntry,
                method: str,
                url: str,
                **kwargs,
                ) -> Response | None:
        key = entry.get('site_config').get('key')
        try:
            return super().request(entry, 'POST', url, headers={'x-api-key': key})
        except Exception as e:
            entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=url, error=e))

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        return

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'key': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def reseed_build_entry(self, entry: Entry, config: dict, site: dict, passkey: dict, torrent_id: str) -> None:
        record = url_recorder.load_record(entry['class_name'])
        now = datetime.datetime.now()
        expire = datetime.timedelta(days=7)
        if (torrent := record.get(torrent_id)) and parse(torrent['expire']) > now - expire:
            entry['url'] = torrent['url']
            return

        key = passkey.get('key')
        response = request('POST', urljoin(self.URL, self.GEN_DL_TOKEN), headers={'x-api-key': key},
                           data={'id': torrent_id}, timeout=60)
        if response.status_code == 200:
            if response.json().get('code') != 0:
                entry.fail(response.json().get('message'))
            else:
                entry['url'] = response.json().get('data')
                record[torrent_id] = {'url': entry['url'], 'expire': (now + expire).strftime('%Y-%m-%d')}
                url_recorder.save_record(entry['class_name'], record)

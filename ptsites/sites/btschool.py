from __future__ import annotations

import re
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.reseed import ReseedPasskey
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://pt.btschool.club/'
    USER_CLASSES: Final = {
        'downloaded': [1099511627776, 10995116277760],
        'share_ratio': [3.05, 4.55],
        'points': [600000, 1000000],
        'days': [280, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/index.php?action=addbonus',
                method=self.sign_in_by_location,
                succeed_regex=['欢迎回来'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            ),
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': '做种积分: ([\\d.,]+)',
                }
            }
        })
        return selector

    def sign_in_by_location(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        response = self.request(entry, 'get', work.url)
        reload__net_state = check_network_state(entry, work.url, response)
        if reload__net_state != NetworkState.SUCCEED:
            return None
        content = net_utils.decode(response)
        location_search = re.search('(?<=window\\.location=).*?(?=;)', content)
        if not location_search:
            return response
        location_url = re.sub('["+ ]', '', location_search.group(0))
        work.url = urljoin(MainClass.URL, location_url)
        return self.sign_in_by_get(entry, config, work)

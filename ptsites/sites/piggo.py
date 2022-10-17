from __future__ import annotations

from typing import Final

import requests
from requests import Response
from requests.adapters import HTTPAdapter

from ..base.entry import SignInEntry
from ..base.request import cf_detected, NetworkState
from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://piggo.me/'
    USER_CLASSES: Final = {
        'downloaded': [size(2, 'TiB'), size(6, 'TiB')],
        'share_ratio': [4, 6],
        'points': [400000, 1000000],
        'days': [280, 700]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'table': '#outer table.main'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': (r'(做种积分).*?([\d,.]+)', 2)
                }
            }
        })
        return selector

    def request(self,
                entry: SignInEntry,
                method: str,
                url: str,
                **kwargs,
                ) -> Response | None:
        if not self.session:
            self.session = requests.Session()
            if entry_headers := entry.get('headers'):
                self.session.headers.update(entry_headers)
            if entry_cookie := entry.get('cookie'):
                self.session.cookies.update(net_utils.cookie_str_to_dict(entry_cookie))
            self.session.mount('http://', HTTPAdapter(max_retries=2))
            self.session.mount('https://', HTTPAdapter(max_retries=2))
        try:
            response: Response = self.session.request(method, url, timeout=60, **kwargs)
            if cf_detected(response):
                entry.fail_with_prefix('Detected CloudFlare DDoS-GUARD')
            elif response is not None and response.status_code != 200:
                if not (response.status_code == 500 and 'messages.php' in response.url):
                    entry.fail_with_prefix(f'response.status_code={response.status_code}')
            entry['session_cookie'] = (' '.join(list(map(lambda x: f'{x[0]}={x[1]};', self.session.cookies.items()))))
            return response
        except Exception as e:
            entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=url, error=e))
        return None

from __future__ import annotations

import re
from enum import Enum

import requests
from requests import Response
from requests.adapters import HTTPAdapter

from .entry import SignInEntry
from .work import Work
from ..utils import net_utils


class NetworkState(Enum):
    SUCCEED = 'Succeed'
    URL_REDIRECT = 'Url: {original_url} redirect to {redirect_url}'
    NETWORK_ERROR = 'Network error: url: {url}, error: {error}'


def check_network_state(entry: SignInEntry,
                        param: Work | str | list[str],
                        response: Response | None,
                        content: str | None = None,
                        check_content=False,
                        ) -> NetworkState:
    urls = param
    if isinstance(param, Work):
        urls = param.response_urls
    elif isinstance(param, str):
        urls = [param]
    if response is None or (check_content and content is None):
        entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=urls[0], error='Response is None'))
        return NetworkState.NETWORK_ERROR
    if response.url not in urls:
        entry.fail_with_prefix(
            NetworkState.URL_REDIRECT.value.format(original_url=urls[0], redirect_url=response.url))
        return NetworkState.URL_REDIRECT
    return NetworkState.SUCCEED


def cf_detected(response: Response) -> bool:
    if response is not None:
        return bool(re.search(r'security by.*Cloudflare</a>', response.text, flags=re.DOTALL))


class Request:

    def __init__(self):
        self.session = None

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
                entry.fail_with_prefix(f'url: {url} detected CloudFlare DDoS-GUARD')
            elif response is not None and response.status_code != 200:
                entry.fail_with_prefix(f'url: {url} response.status_code={response.status_code}')
            entry['session_cookie'] = (' '.join(list(map(lambda x: f'{x[0]}={x[1]};', self.session.cookies.items()))))
            return response
        except Exception as e:
            entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=url, error=e))
        return None

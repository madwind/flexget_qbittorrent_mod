import datetime
import re
from enum import Enum
from re import Match
from typing import Callable, Union
from urllib.parse import urljoin

import requests
from dateutil.parser import parse
from flexget.entry import Entry
from flexget.utils.soup import get_soup
from loguru import logger
from requests import Response
from requests.adapters import HTTPAdapter

from ..utils import net_utils, url_recorder

try:
    from pyppeteer import launch, chromium_downloader
    from pyppeteer_stealth import stealth
except ImportError:
    launch = None
    stealth = None


class SignState(Enum):
    NO_SIGN_IN = 'No sign in'
    SUCCEED = 'Succeed'
    WRONG_ANSWER = 'Wrong answer'
    SIGN_IN_FAILED = 'Sign in failed, {}'
    UNKNOWN = 'Unknown, url: {}'


class NetworkState(Enum):
    SUCCEED = 'Succeed'
    URL_REDIRECT = 'Url: {original_url} redirect to {redirect_url}'
    NETWORK_ERROR = 'Network error: url: {url}, error: {error}'


class NetworkErrorReason(Enum):
    DDOS_PROTECTION_BY_CLOUDFLARE = 'DDoS protection by .+?Cloudflare'
    SERVER_LOAD_TOO_HIGH = r'<h3 align=center>(服务器负载过|伺服器負載過)高，正在重(试|試)，(请|請)稍(后|後)\.\.\.</h3>'
    CONNECTION_TIMED_OUT = r'<h2 class="text-gray-600 leading-1\.3 text-3xl font-light">Connection timed out</h2>'
    THE_WEB_SERVER_REPORTED_A_BAD_GATEWAY_ERROR = r'<p>The web server reported a bad gateway error\.</p>'
    WEB_SERVER_IS_DOWN = '站点关闭维护中，请稍后再访问...谢谢|站點關閉維護中，請稍後再訪問...謝謝|Web server is down'


class Work:
    def __init__(self, url: str = None, method: str = None, data=None, succeed_regex: list[Union[str, tuple]] = None,
                 fail_regex: str = None,
                 check_state: tuple = None, response_urls=None, is_base_content=False, **kwargs):
        self.url: str = url
        self.method = method
        self.data = data
        self.succeed_regex = succeed_regex
        self.fail_regex = fail_regex
        self.check_state = check_state
        self.is_base_content = is_base_content
        self.response_urls = response_urls if response_urls else [url]
        for key, value in kwargs.items():
            self.__setattr__(key, value)


class SiteBase:
    URL: str = None
    USER_CLASSES: dict = None
    DOWNLOAD_PAGE = 'download.php?id={torrent_id}'

    def __init__(self):
        self.requests = None

    @classmethod
    def build_sign_in_schema(cls):
        return {cls.get_module_name(): {'type': 'string'}}

    @classmethod
    def build_reseed_schema(cls):
        return {cls.get_module_name(): {'type': 'string'}}

    @classmethod
    def get_module_name(cls):
        return cls.__module__.rsplit('.', maxsplit=1)[-1]

    @classmethod
    def build_sign_in_entry(cls, entry: Entry, config: dict) -> None:
        entry['url'] = cls.URL
        site_config: Union[str, dict] = entry['site_config']
        headers: dict = {
            'user-agent': config.get('user-agent'),
            'referer': entry['url'],
            'accept-encoding': 'gzip, deflate, br',
        }
        cookie: Union[str, None] = None
        if isinstance(site_config, str):
            cookie = site_config
        elif isinstance(site_config, dict):
            cookie = site_config.get('cookie')
        if cookie:
            entry['cookie'] = cookie
        entry['headers'] = headers
        entry['user_classes'] = cls.USER_CLASSES

    def build_login_workflow(self, entry: Entry, config: dict) -> list[Work]:
        return []

    def build_login_data(self, login: dict, last_content) -> dict:
        return {}

    def build_workflow(self, entry: Entry, config: dict) -> list[Work]:
        return []

    def build_selector(self):
        return {}

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def get_message(self, entry, config: dict) -> None:
        entry['result'] += '(TODO: Message)'

    def sign_in(self, entry, config: dict) -> None:
        workflow: list[Work] = []
        if not entry.get('cookie'):
            workflow.extend(self.build_login_workflow(entry, config))
        workflow.extend(self.build_workflow(entry, config))
        if not entry.get('url') or not workflow:
            entry.fail_with_prefix(f"site: {entry['site_name']} url or workflow is empty")
            return
        last_content: Union[str, None] = None
        last_response: Union[Response, None] = None
        for work in workflow:
            work.url = urljoin(entry['url'], work.url)
            work.response_urls = list(map(lambda response_url: urljoin(entry['url'], response_url), work.response_urls))
            method_name = f"sign_in_by_{work.method}"
            if method := getattr(self, method_name, None):
                if work.method == 'get' and last_response and net_utils.url_equal(
                        work.url, last_response.url) and work.is_base_content:
                    entry['base_content'] = last_content
                else:
                    last_response: Response = method(entry, config, work, last_content)
                    if last_response == 'skip':
                        continue
                    if (last_content := net_utils.decode(last_response)) and work.is_base_content:
                        entry['base_content'] = last_content
                if work.check_state:
                    if not self.check_state(entry, work, last_response, last_content):
                        return

    @classmethod
    def build_reseed_entry(cls, entry: Entry, config: dict, site, passkey, torrent_id) -> None:
        cls.build_reseed_entry_from_url(entry, config, site, passkey, torrent_id)

    @classmethod
    def build_reseed_entry_from_url(cls, entry: Entry, config: dict, site, passkey, torrent_id) -> None:
        if isinstance(passkey, dict):
            user_agent: str = config.get('user-agent')
            cookie: str = passkey.get('cookie')
            entry['headers']: dict = {
                'user-agent': user_agent,
            }
            entry['cookie'] = cookie
            download_page = cls.DOWNLOAD_PAGE.format(torrent_id=torrent_id)
        else:
            download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = f"https://{site['base_url']}/{download_page}"

    @classmethod
    def build_reseed_from_page(cls, entry: Entry, config: dict, passkey, torrent_id, base_url, torrent_page_url,
                               url_regex) -> None:
        record = url_recorder.load_record(entry['class_name'])
        now = datetime.datetime.now()
        expire = datetime.timedelta(days=7)
        if torrent := record.get(torrent_id):
            if parse(torrent['expire']) > now - expire:
                entry['url'] = torrent['url']
                return
        download_url = ''
        try:
            torrent_page_url = urljoin(base_url, torrent_page_url.format(torrent_id=torrent_id))
            session = requests.Session()
            user_agent = config.get('user-agent')
            cookie = passkey.get('cookie')
            headers = {
                'user-agent': user_agent,
                'referer': base_url
            }
            session.headers.update(headers)
            session.cookies.update(net_utils.cookie_str_to_dict(cookie))
            response = session.get(torrent_page_url, timeout=60)
            if response is not None and response.status_code == 200:
                if re_search := re.search(url_regex, response.text):
                    download_url = urljoin(base_url, re_search.group())
        except Exception as e:
            logger.warning(e)
        if not download_url:
            entry.fail(f"site:{entry['class_name']} can not found download url from {torrent_page_url}")
        entry['url'] = download_url
        record[torrent_id] = {'url': download_url, 'expire': (now + expire).strftime('%Y-%m-%d')}
        url_recorder.save_record(entry['class_name'], record)

    def _request(self, entry, method: str, url: str, **kwargs) -> Union[Response, None]:
        if not self.requests:
            self.requests = requests.Session()
            if entry_headers := entry.get('headers'):
                self.requests.headers.update(entry_headers)
            if entry_cookie := entry.get('cookie'):
                self.requests.cookies.update(net_utils.cookie_str_to_dict(entry_cookie))
            self.requests.mount('http://', HTTPAdapter(max_retries=2))
            self.requests.mount('https://', HTTPAdapter(max_retries=2))
        try:
            response: Response = self.requests.request(method, url, timeout=60, **kwargs)
            if response is not None and response.status_code != 200:
                entry.fail_with_prefix(f'response.status_code={response.status_code}')
            return response
        except Exception as e:
            entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=url, error=e))
        return None

    def sign_in_by_get(self, entry, config: dict, work: Work, last_content: Union[str, None] = None) -> Response:
        return self._request(entry, 'get', work.url)

    def sign_in_by_post(self, entry, config: dict, work: Work,
                        last_content: Union[str, None] = None) -> Union[Response, None]:
        data = {}
        for key, regex in work.data.items():
            if key == 'fixed':
                net_utils.dict_merge(data, regex)
            else:
                value_search: Match = re.search(regex, last_content)
                if value_search:
                    data[key] = value_search.group()
                else:
                    entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, work.url))
                    return
        return self._request(entry, 'post', work.url, data=data)

    def sign_in_by_login(self, entry, config: dict, work: Work, last_content: str) -> Union[Response, None]:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        return self._request(entry, 'post', work.url, data=self.build_login_data(login, last_content))

    def get_user_id(self, entry, user_id_selector: str, base_content: str) -> Union[str, None]:
        if isinstance(user_id_selector, str):
            user_id_match: Match = re.search(user_id_selector, base_content)
            if user_id_match:
                return user_id_match.group(1)
            else:
                entry.fail_with_prefix('User id not found.')
                logger.error(f'site: {entry["site_name"]} User id not found. content: {base_content}')
                return
        else:
            entry.fail_with_prefix('user_id_selector is not str.')
            logger.error(f'site: {entry["site_name"]} user_id_selector is not str.')
            return

    def get_details_base(self, entry, config: str, selector: dict) -> None:
        if not (base_content := entry.get('base_content')):
            entry.fail_with_prefix('base_content is None.')
            return
        user_id = ''
        user_id_selector: str = selector.get('user_id')
        if user_id_selector and not (user_id := self.get_user_id(entry, user_id_selector, base_content)):
            return
        details_text = ''
        detail_sources = selector.get('detail_sources')
        for detail_source in detail_sources.values():
            if detail_source.get('link'):
                detail_source['link'] = urljoin(entry['url'], detail_source['link'].format(user_id))
                detail_response = self._request(entry, 'get', detail_source['link'])
                network_state = self.check_network_state(entry, detail_source['link'], detail_response)
                if network_state != NetworkState.SUCCEED:
                    return
                detail_content = net_utils.decode(detail_response)
            else:
                detail_content = base_content
            do_not_strip = detail_source.get('do_not_strip')
            elements = detail_source.get('elements')
            if elements:
                soup = get_soup(detail_content)
                for name, sel in elements.items():
                    if sel:
                        details_info = soup.select_one(sel)
                        if details_info:
                            if do_not_strip:
                                details_text = details_text + str(details_info)
                            else:
                                details_text = details_text + details_info.text
                        else:
                            entry.fail_with_prefix(f'Element: {name} not found.')
                            logger.error('site: {} element: {} not found, selector: {}, soup: {}',
                                         entry['site_name'],
                                         name, sel, soup)
                            return
            else:
                details_text = details_text + detail_content
        if details_text:
            logger.debug(details_text)
            details = {}
            for detail_name, detail_config in selector['details'].items():
                detail_value = self.get_detail_value(details_text, detail_config)
                if not detail_value:
                    entry.fail_with_prefix(f'detail: {detail_name} not found.')
                    logger.error(
                        f"Details=> site: {entry['site_name']}, regex: {detail_config['regex']}，details_text: {details_text}")
                    return
                details[detail_name] = detail_value
            entry['details'] = details
        else:
            entry.fail_with_prefix('details_text is None.')

    def check_state(self, entry: Entry, work: Work, response: Response, content: str) -> bool:
        if entry.failed:
            return False
        check_type, check_result = work.check_state
        if check := getattr(self, f"check_{check_type}_state", None):
            return check(entry, work, response, content) == check_result

    def check_network_state(self, entry, param: Union[Work, str], response: Response,
                            content: str = None, check_content=False) -> NetworkState:
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

    def check_sign_in_state(self, entry, work: Work, response: Response,
                            content: str) -> Union[NetworkState, SignState]:
        network_state = self.check_network_state(entry, work, response, content=content, check_content=True)
        if network_state != NetworkState.SUCCEED:
            return network_state

        if not (succeed_regex := work.succeed_regex):
            entry['result'] = SignState.SUCCEED.value
            return SignState.SUCCEED

        for regex in succeed_regex:
            if isinstance(regex, str):
                regex = (regex, 0)
            regex, group_index = regex
            if succeed_msg := re.search(regex, content):
                entry['result'] = re.sub('<.*?>|&shy;|&nbsp;', '', succeed_msg.group(group_index))
                return SignState.SUCCEED
        if fail_regex := work.fail_regex:
            if re.search(fail_regex, content):
                return SignState.WRONG_ANSWER

        for reason in NetworkErrorReason:
            if re.search(reason.value, content):
                entry.fail_with_prefix(
                    NetworkState.NETWORK_ERROR.value.format(url=work.url, error=reason.name.title()))
                return NetworkState.NETWORK_ERROR

        if check_state := work.check_state:
            if check_state[1] != SignState.NO_SIGN_IN:
                logger.warning(f'no sign in, regex: {succeed_regex}, content: {content}')

        return SignState.NO_SIGN_IN

    def check_final_state(self, entry, work: Work, response: Response, content: str) -> SignState:
        sign_in_state: SignState = self.check_sign_in_state(entry, work, response, content)
        if sign_in_state == SignState.NO_SIGN_IN:
            entry.fail_with_prefix(SignState.SIGN_IN_FAILED.value.format('no sign in'))
            return SignState.SIGN_IN_FAILED
        return sign_in_state

    def get_detail_value(self, content: str, detail_config: dict) -> Union[str, None]:
        if detail_config is None:
            return '*'
        regex: Union[str, tuple] = detail_config['regex']
        group_index = 1
        if isinstance(regex, tuple):
            regex, group_index = regex
        detail_match: Match = re.search(regex, content, re.DOTALL)
        if not detail_match:
            return None
        detail = detail_match.group(group_index)
        if not detail:
            return None
        detail = detail.replace(',', '')
        handle: Callable = detail_config.get('handle')
        if handle:
            detail = handle(detail)
        return str(detail)

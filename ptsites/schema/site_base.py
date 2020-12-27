import asyncio
import datetime
import re
from enum import Enum
from urllib.parse import urljoin

import chardet
import requests
from dateutil.parser import parse
from flexget.utils.soup import get_soup
from loguru import logger
from requests.adapters import HTTPAdapter
from ..utils.url_recorder import UrlRecorder

try:
    import brotli
except ImportError:
    brotli = None

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
    DDoS_protection_by_Cloudflare = 'DDoS protection by .+?Cloudflare'
    Server_load_too_high = '<h3 align=center>服务器负载过高，正在重试，请稍后\\.\\.\\.</h3>'
    Connection_timed_out = '<h2 class="text-gray-600 leading-1\\.3 text-3xl font-light">Connection timed out</h2>'


class Work:
    def __init__(self, url=None, method=None, data=None, succeed_regex=None, fail_regex=None,
                 check_state=None, response_urls=None, is_base_content=False, **kwargs):
        self.url = url
        self.method = method
        self.data = data
        self.succeed_regex = succeed_regex
        self.fail_regex = fail_regex
        self.check_state = check_state
        self.is_base_content = is_base_content
        self.response_urls = response_urls if response_urls else [url]
        for k, v in kwargs.items():
            self.__setattr__(k, v)


class SiteBase:
    CLOUDFLARE = False
    URL = ''

    def __init__(self):
        self.requests = None

    @classmethod
    def build_sign_in(cls, entry, config):
        site_config = entry['site_config']
        entry['url'] = cls.URL
        entry['workflow'] = cls.build_workflow()
        entry['user_classes'] = getattr(cls, 'USER_CLASSES', None)
        headers = {
            'user-agent': config.get('user-agent'),
            'referer': entry['url']
        }
        cookie = None
        if isinstance(site_config, str):
            cookie = site_config
        elif isinstance(site_config, dict):
            cookie = site_config.get('cookie')
        if cookie:
            headers['cookie'] = cookie
        entry['headers'] = headers

    @classmethod
    def build_workflow(cls):
        pass

    def sign_in(self, entry, config):
        if not entry['url'] or not entry['workflow']:
            entry.fail_with_prefix(f"site: {entry['site_name']} url or workflow is empty")
            return
        last_content = None
        for work in entry['workflow']:
            self.work_urljoin(work, entry['url'])
            method_name = f"sign_in_by_{work.method}"
            if method := getattr(self, method_name, None):
                last_response = method(entry, config, work, last_content)
                if (last_content := self._decode(last_response)) and work.is_base_content:
                    entry['base_content'] = last_content
                if work.check_state:
                    if not self.check_state(entry, work, last_response, last_content):
                        return

    def work_urljoin(self, work, url):
        for work_key, work_value in work.__dict__.items():
            if work_key.endswith('url'):
                setattr(work, work_key, urljoin(url, work_value))
            elif work_key.endswith('urls'):
                setattr(work, work_key, list(map(lambda path: urljoin(url, path), work_value)))

    @staticmethod
    def build_reseed(entry, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = 'https://{}/{}'.format(site['base_url'], download_page)

    @staticmethod
    def build_reseed_from_page(entry, passkey, torrent_id, base_url, torrent_page_url, url_regex):
        record = UrlRecorder.load_record(entry['class_name'])
        now = datetime.datetime.now()
        expire = datetime.timedelta(days=7)
        if torrent := record.get(torrent_id):
            if parse(torrent['expire']) > now - expire:
                entry['url'] = torrent['url']
            return
        download_url = ''
        try:
            torrent_page_url = urljoin(base_url, torrent_page_url.format(torrent_id))
            response = requests.get(torrent_page_url, headers=passkey['headers'], timeout=30)
            if response.status_code == 200:
                re_search = re.search(url_regex, response.text)
                if re_search:
                    download_url = urljoin(base_url, re_search.group())
        except Exception as e:
            logger.warning(str(e.args))
        if not download_url:
            entry.fail(f"site:{entry['class_name']} can not found download url from {torrent_page_url}")
        entry['url'] = download_url
        record[torrent_id] = {'url': download_url, 'expire': (now + expire).strftime('%Y-%m-%d')}
        UrlRecorder.save_record(entry['class_name'], record)

    def _request(self, entry, method, url, **kwargs):
        if not self.requests:
            self.requests = requests.Session()
            if headers := entry.get('headers'):
                if brotli:
                    headers['accept-encoding'] = 'gzip, deflate, br'
                if entry.get('cf'):
                    cookie = asyncio.run(
                        SiteBase.get_cf_cookie(entry, headers))
                    headers['cookie'] = cookie
                self.requests.headers.update(headers)
            self.requests.mount('http://', HTTPAdapter(max_retries=2))
            self.requests.mount('https://', HTTPAdapter(max_retries=2))
        try:
            response = self.requests.request(method, url, allow_redirects=False, timeout=60, **kwargs)
            if response.status_code == 302:
                redirect_url = urljoin(url, response.headers['Location'])
                response = self._request(entry, 'get', redirect_url, **kwargs)
            return response
        except Exception as e:
            entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=url, error=str(e.args)))
        return None

    def sign_in_by_get(self, entry, config, work, last_content=None):
        return self._request(entry, 'get', work.url)

    def sign_in_by_post(self, entry, config, work, last_content=None):
        data = {}
        for key, regex in work.data.items():
            if key == 'fixed':
                self.dict_merge(data, regex)
            else:
                value_search = re.search(regex, last_content)
                if value_search:
                    data[key] = value_search.group()
                else:
                    entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, work.url))
                    return
        return self._request(entry, 'post', work.url, data=data)

    def get_details_base(self, entry, config, selector):
        if not (base_content := entry.get('base_content')):
            entry.fail_with_prefix('base_content is None.')
            return
        user_id = ''
        user_id_selector = selector.get('user_id')
        if user_id_selector:
            user_id_match = re.search(user_id_selector, base_content)
            if user_id_match:
                user_id = user_id_match.group(1)
            else:
                entry.fail_with_prefix('User id not found.')
                logger.debug('site: {} User id not found. content: {}'.format(entry['site_name'], base_content))
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
                detail_content = self._decode(detail_response)
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
                            entry.fail_with_prefix('Element: {} not found.'.format(name))
                            logger.error('site: {} element: {} not found, selecotr: {}, soup: {}',
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
                    logger.debug(
                        f"Details=> site: {entry['site_name']}, regex: {detail_config['regex']}，details_text: {details_text}")
                    return
                details[detail_name] = detail_value
            entry['details'] = details
        else:
            entry.fail_with_prefix('details_text is None.')

    def check_state(self, entry, work, response, content):
        if entry.failed:
            return False
        check_type, check_result = work.check_state
        if check := getattr(self, f"check_{check_type}_state", None):
            if check(entry, work, response, content) != check_result:
                return False
            else:
                return True

    def check_network_state(self, entry, param, response, content=None, check_content=False):
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

    def check_sign_in_state(self, entry, work, response, content):
        network_state = self.check_network_state(entry, work, response, content=content, check_content=True)
        if network_state != NetworkState.SUCCEED:
            return network_state

        if not (succeed_regex := work.succeed_regex):
            entry['result'] = SignState.SUCCEED.value
            return SignState.SUCCEED
        if isinstance(succeed_regex, str):
            succeed_regex = [succeed_regex]

        for regex in succeed_regex:
            if succeed_msg := re.search(regex, content):
                entry['result'] = re.sub('<.*?>|&shy;|&nbsp;', '', succeed_msg.group())
                return SignState.SUCCEED

        if fail_regex := work.fail_regex:
            if re.search(fail_regex, content):
                return SignState.WRONG_ANSWER

        for reason in NetworkErrorReason:
            if re.search(reason.value, content):
                entry.fail_with_prefix(
                    NetworkState.NETWORK_ERROR.value.format(url=work.url, error=reason.name))
                return NetworkState.NETWORK_ERROR

        logger.warning('no sign in, content: {}'.format(content))

        return SignState.NO_SIGN_IN

    def check_final_state(self, entry, work, response, content):
        sign_in_state = self.check_sign_in_state(entry, work, response, content)
        if sign_in_state == SignState.NO_SIGN_IN:
            entry.fail_with_prefix(SignState.SIGN_IN_FAILED.value.format('no sign in'))
            return SignState.SIGN_IN_FAILED
        return sign_in_state

    def _decode(self, response):
        if response is None:
            return None
        content = response.content
        charset_encoding = chardet.detect(content).get('encoding')
        if charset_encoding == 'ascii':
            charset_encoding = 'unicode_escape'
        elif charset_encoding == 'Windows-1254':
            charset_encoding = 'utf-8'
        return content.decode(charset_encoding if charset_encoding else 'utf-8', 'ignore')

    def dict_merge(self, dict1, dict2):
        for i in dict2:
            if isinstance(dict1.get(i), dict) and isinstance(dict2.get(i), dict):
                self.dict_merge(dict1[i], dict2[i])
            else:
                dict1[i] = dict2[i]

    def get_detail_value(self, content, detail_config):
        if detail_config is None:
            return '*'
        regex = detail_config['regex']
        group_index = 1
        if isinstance(regex, tuple):
            regex, group_index = regex
        detail_match = re.search(regex, content, re.DOTALL)
        if not detail_match:
            return None
        detail = detail_match.group(group_index)
        if not detail:
            return None
        detail = detail.replace(',', '')
        handle = detail_config.get('handle')
        if handle:
            detail = handle(detail)
        return str(detail)

    @staticmethod
    async def get_cf_cookie(entry, headers):
        if not (launch and stealth):
            entry.fail_with_prefix('Dependency does not exist: [pyppeteer, pyppeteer_stealth]')
            return headers
        browser = await launch(headless=True, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
                               args=['--no-sandbox'])
        page = await browser.newPage()
        await stealth(page)
        await page.setUserAgent(headers.get('user_agent'))
        cookie_remove_cf = ';'.join(
            list(filter(lambda x: not re.search('__cfduid|cf_clearance|__cf_bm', x), headers.get('cookie').split(';'))))
        await page.setExtraHTTPHeaders({'cookie': cookie_remove_cf})
        await page.goto(entry['url'])
        await asyncio.sleep(10)
        page_cookie = await page.cookies()
        cf_cookie = cookie_remove_cf + ';' + ';'.join(
            list(map(lambda c: f"{c['name']}={c['value']}", page_cookie)))
        await browser.close()
        return cf_cookie

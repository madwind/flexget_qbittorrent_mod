from __future__ import annotations

import datetime
import re
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from dateutil.parser import parse
from flexget.entry import Entry
from flexget.utils.soup import get_soup
from loguru import logger
from requests import Response

from ..base.detail import Detail
from ..base.entry import SignInEntry
from ..base.message import Message
from ..base.request import Request, NetworkState, check_network_state
from ..base.reseed import Reseed
from ..base.sign_in import Work, check_state, SignIn
from ..utils import net_utils, url_recorder
from ..utils.net_utils import get_module_name, cookie_str_to_dict


class PrivateTorrent(Request, SignIn, Detail, Message, Reseed, ABC):
    @property
    @abstractmethod
    def URL(self) -> str:
        pass

    @property
    def USER_CLASSES(self) -> dict[str, list[float]]:
        return {}

    DOWNLOAD_PAGE_TEMPLATE = 'download.php?id={torrent_id}'

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {get_module_name(cls): {'type': 'string'}}

    @classmethod
    def sign_in_build_entry(cls, entry: SignInEntry, config: dict) -> None:
        entry['url'] = cls.URL
        site_config: str | dict = entry['site_config']
        headers: dict = {
            'user-agent': config.get('user-agent'),
            'referer': entry['url'],
            'accept-encoding': 'gzip, deflate, br',
        }
        cookie: str | None = None
        if isinstance(site_config, str):
            cookie = site_config
        elif isinstance(site_config, dict):
            cookie = site_config.get('cookie')
        if cookie:
            entry['cookie'] = cookie
        entry['headers'] = headers
        entry['user_classes'] = cls().USER_CLASSES

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {}

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return []

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return []

    def sign_in(self, entry: SignInEntry, config: dict) -> None:
        workflow: list[Work] = []
        if not entry.get('cookie'):
            workflow.extend(self.sign_in_build_login_workflow(entry, config))
        workflow.extend(self.sign_in_build_workflow(entry, config))
        if not entry.get('url') or not workflow:
            entry.fail_with_prefix(f"site: {entry['site_name']} url or workflow is empty")
            return
        last_work: Work | None = None
        last_response: Response | None = None
        last_content: str | None = None
        for work in workflow:
            work.url = urljoin(entry['url'], work.url)
            work.response_urls = list(map(lambda response_url: urljoin(entry['url'], response_url), work.response_urls))

            if work.use_last_content and last_work:
                work.response_urls = last_work.response_urls
            else:
                last_response = work.method(entry, config, work, last_content)
                last_content = net_utils.decode(last_response)

            if work.is_base_content:
                entry['base_content'] = last_content
            if not check_state(entry, work, last_response, last_content):
                return
            last_work = work

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        entry['result'] += '(TODO: Message)'

    @property
    def details_selector(self) -> dict:
        return {}

    def get_user_id(self, entry: SignInEntry, user_id_selector: str, base_content: str) -> str | None:
        if user_id_match := re.search(user_id_selector, base_content):
            return user_id_match.group(1)
        entry.fail_with_prefix('User id not found.')
        logger.error(f'site: {entry["site_name"]} User id not found. content: {base_content}')
        return None

    def get_detail_value(self, content: str, detail_config: dict) -> str | None:
        if detail_config is None:
            return '*'
        regex: str | tuple = detail_config['regex']
        group_index = 1
        if isinstance(regex, tuple):
            regex, group_index = regex
        if not (detail_match := re.search(regex, content, re.DOTALL)):
            return None
        if not (detail := detail_match.group(group_index)):
            return None
        detail = detail.replace(',', '')
        if handle := detail_config.get('handle'):
            detail = handle(detail)
        return str(detail)

    def get_details_base(self, entry: SignInEntry, config, selector: dict) -> None:
        if not (base_content := entry.get('base_content')):
            entry.fail_with_prefix('base_content is None.')
            return
        user_id = ''
        if (user_id_selector := selector.get('user_id')) and not (
                user_id := self.get_user_id(entry, user_id_selector, base_content)):
            return
        details_text = ''
        for detail_source in selector['detail_sources'].values():
            if detail_source.get('link'):
                detail_source['link'] = urljoin(entry['url'], detail_source['link'].format(user_id))
                detail_response = self.request(entry, 'get', detail_source['link'])
                network_state = check_network_state(entry, detail_source['link'], detail_response)
                if network_state != NetworkState.SUCCEED:
                    return
                detail_content = net_utils.decode(detail_response)
            else:
                detail_content = base_content
            if elements := detail_source.get('elements'):
                soup = get_soup(detail_content)
                for name, sel in elements.items():
                    if sel:
                        if details_info := soup.select_one(sel):
                            details_text += str(details_info) if detail_source.get(
                                'do_not_strip') else details_info.text
                        else:
                            entry.fail_with_prefix(f'Element: {name} not found.')
                            logger.error('site: {} element: {} not found, selector: {}, soup: {}',
                                         entry['site_name'],
                                         name, sel, soup)
                            return
            else:
                details_text += detail_content
        if not details_text:
            entry.fail_with_prefix('details_text is None.')
            return
        logger.debug(details_text)
        details = {}
        for detail_name, detail_config in selector['details'].items():
            if not (detail_value := self.get_detail_value(details_text, detail_config)):
                entry.fail_with_prefix(f'detail: {detail_name} not found.')
                logger.error(
                    f"Details=> site: {entry['site_name']}, regex: {detail_config['regex']}，details_text: {details_text}")
                return
            details[detail_name] = detail_value
        entry['details'] = details

    def get_details(self, entry: SignInEntry, config: dict) -> None:
        self.get_details_base(entry, config, self.details_selector)

    @classmethod
    def reseed_build_schema(cls):
        return {get_module_name(cls): {'type': 'string'}}

    @classmethod
    def reseed_build_entry_from_url(cls, entry: Entry, config: dict, site: dict, passkey: dict | str,
                                    torrent_id) -> None:
        if isinstance(passkey, dict):
            user_agent = config.get('user-agent')
            cookie = passkey.get('cookie')
            entry['headers'] = {
                'user-agent': user_agent,
            }
            entry['cookie'] = cookie
            download_page = cls.DOWNLOAD_PAGE_TEMPLATE.format(torrent_id=torrent_id)
        else:
            download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = f"https://{site['base_url']}/{download_page}"

    @classmethod
    def reseed_build_entry_from_page(cls, entry: Entry, config: dict, passkey, torrent_id, base_url,
                                     torrent_page_url, url_regex) -> None:
        record = url_recorder.load_record(entry['class_name'])
        now = datetime.datetime.now()
        expire = datetime.timedelta(days=7)
        if (torrent := record.get(torrent_id)) and parse(torrent['expire']) > now - expire:
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
            session.cookies.update(cookie_str_to_dict(cookie))
            response = session.get(torrent_page_url, timeout=60)
            if response is not None and response.status_code == 200 and (
                    re_search := re.search(url_regex, response.text)):
                download_url = urljoin(base_url, re_search.group())
        except Exception as e:
            logger.warning(e)
        if not download_url:
            entry.fail(f"site:{entry['class_name']} can not found download url from {torrent_page_url}")
        entry['url'] = download_url
        record[torrent_id] = {'url': download_url, 'expire': (now + expire).strftime('%Y-%m-%d')}
        url_recorder.save_record(entry['class_name'], record)

    @classmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site, passkey, torrent_id) -> None:
        cls.reseed_build_entry_from_url(entry, config, site, passkey, torrent_id)

    def sign_in_by_get(self, entry: SignInEntry, config: dict, work: Work, last_content: str = None) -> Response | None:
        return self.request(entry, 'get', work.url)

    def sign_in_by_post(self, entry: SignInEntry, config: dict, work: Work,
                        last_content: str = None) -> Response | None:
        data = {}
        for key, regex in work.data.items():
            if key == 'fixed':
                net_utils.dict_merge(data, regex)
            elif value_search := re.search(regex, last_content):
                data[key] = value_search.group()
            else:
                entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, work.url))
                return None
        return self.request(entry, 'post', work.url, data=data)

    def sign_in_by_login(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return None
        return self.request(entry, 'post', work.url, data=self.sign_in_build_login_data(login, last_content))

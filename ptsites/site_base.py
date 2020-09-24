import itertools
import json
import os
import re
import time
from enum import Enum
from pathlib import Path
from urllib.parse import urljoin

import chardet
import requests
from flexget import plugin
from flexget.utils.soup import get_soup
from loguru import logger
from requests.adapters import HTTPAdapter

try:
    import brotli
except ImportError:
    brotli = None

try:
    from selenium import webdriver
    from selenium.webdriver import DesiredCapabilities
except ImportError:
    webdriver = None
    DesiredCapabilities = None

try:
    from aip import AipOcr
except ImportError:
    AipOcr = None

try:
    from PIL import Image
except ImportError:
    Image = None


class SignState(Enum):
    NO_SIGN_IN = 'No sign in'
    SUCCEED = 'Succeed'
    WRONG_ANSWER = 'Wrong answer'
    URL_REDIRECT = 'Url: {} redirect to {}'
    UNKNOWN = 'Unknown, url: {}'
    NETWORK_ERROR = 'Network error: url: {url}, error: {error}'
    SIGN_IN_FAILED = 'Sign in failed, {}'


class SiteBase:
    def __init__(self):
        self.requests = None

    @staticmethod
    def build_sign_in_entry(entry, config, url, succeed_regex, base_url=None,
                            wrong_regex=None):
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(entry['site_name']))
        entry['url'] = url
        entry['succeed_regex'] = succeed_regex
        if base_url:
            entry['base_url'] = base_url
        if wrong_regex:
            entry['wrong_regex'] = wrong_regex
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': base_url if base_url else url
        }
        entry['headers'] = headers

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id, passkey=passkey)
        entry['url'] = 'https://{}/{}'.format(base_url, download_page)

    def _request(self, entry, method, url, **kwargs):
        if not self.requests:
            self.requests = requests.Session()
            headers = entry['headers']
            if headers:
                if brotli:
                    headers['accept-encoding'] = 'gzip, deflate, br'
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
            entry.fail(entry['prefix'] + '=> ' + SignState.NETWORK_ERROR.value.format(url=url, error=str(e.args)))
        return None

    def sign_in_by_get(self, entry, config):
        entry['base_response'] = response = self._request(entry, 'get', entry['url'])
        self.final_check(entry, response, entry['url'])

    def sign_in_by_post_data(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', entry['base_url'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, entry['base_url'])
        if sign_in_state != SignState.NO_SIGN_IN:
            return
        data = {}
        for key, regex in entry.get('data', {}).items():
            if key == 'fixed':
                self._dict_merge(data, regex)
            else:
                value_search = re.search(regex, base_content)
                if value_search:
                    data[key] = value_search.group()
                else:
                    entry.fail('Cannot find key: {}, url: {}'.format(key, entry['url']))
                    return
        response = self._request(entry, 'post', entry['url'], data=data)
        self.final_check(entry, response, entry['url'])

    def sign_in_by_question(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', entry['url'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, entry['url'])
        if sign_in_state != SignState.NO_SIGN_IN:
            return

        question_element = get_soup(base_content).select_one('input[name="questionid"]')
        if question_element:
            question_id = question_element.get('value')

            local_answer = None

            question_file_path = os.path.dirname(__file__) + '/question.json'
            if Path(question_file_path).is_file():
                with open(question_file_path) as question_file:
                    question_json = json.loads(question_file.read())
            else:
                question_json = {}

            question_extend_file_path = os.path.dirname(__file__) + '/question_extend.json'
            if Path(question_extend_file_path).is_file():
                with open(question_extend_file_path) as question_extend_file:
                    question_extend_json = json.loads(question_extend_file.read())
                os.remove(question_extend_file_path)
            else:
                question_extend_json = {}

            self._dict_merge(question_json, question_extend_json)

            site_question = question_json.get(entry['url'])
            if site_question:
                local_answer = site_question.get(question_id)
            else:
                question_json[entry['url']] = {}

            choice_elements = get_soup(base_content).select('input[name="choice[]"]')
            choices = []
            for choice_element in choice_elements:
                choices.append(choice_element.get('value', ''))

            if choice_elements[0].get('type') == 'radio':
                choice_range = 1
            else:
                choice_range = len(choices)

            answer_list = []

            for i in range(choice_range):
                for arr in itertools.combinations(choices, i + 1):
                    if list(arr) not in answer_list:
                        answer_list.append(list(arr))
            answer_list.reverse()
            if local_answer and local_answer in choices and len(local_answer) <= choice_range:
                answer_list.insert(0, local_answer)
            times = 0
            for answer in answer_list:
                data = {'questionid': question_id, 'choice[]': answer, 'usercomment': '此刻心情:无', 'submit': '提交'}
                response = self._request(entry, 'post', entry['url'], data=data)
                state, content = self.check_sign_in_state(entry, response, entry['url'])
                if state == SignState.SUCCEED:
                    entry['result'] = '{} ( {} attempts.)'.format(entry['result'], times)

                    question_json[entry['url']][question_id] = answer
                    with open(question_file_path, mode='w') as question_file:
                        json.dump(question_json, question_file)
                    logger.info('{}, correct answer: {}', entry['title'], data)
                    return
                times += 1
        entry.fail(SignState.SIGN_IN_FAILED.value.format('No answer.'))

    def get_details_base(self, entry, config, selector):
        detail_sources = selector['detail_sources']

        user_id = ''
        user_id_selector = selector.get('user_id')
        if user_id_selector:
            if not entry.get('base_response'):
                entry.fail('Details=> base_response is None.')
                return
            base_content = self._decode(entry['base_response'])
            user_id_match = re.search(user_id_selector, base_content)
            if user_id_match:
                user_id = user_id_match.group(1)
            else:
                entry.fail('Details=> User id not found.')
                return
        details_text = ''
        for detail_source in detail_sources:
            detail_source['link'] = urljoin(entry['url'], detail_source['link'].format(user_id))
            detail_response = self._request(entry, 'get', detail_source['link'])
            net_state = self.check_net_state(entry, detail_response, detail_source['link'])
            if net_state:
                return
            detail_content = self._decode(detail_response)

            elements = detail_source.get('elements')
            if elements:
                soup = get_soup(self._decode(detail_response))
                for name, sel in elements.items():
                    if sel:
                        details_info = soup.select_one(sel)
                        if details_info:
                            details_text = details_text + details_info.get_text()
                        else:
                            entry.fail('Element: {} not found.'.format(name))
                            logger.error('site: {} element: {} not found, selecotr: {}, soup: {}', entry['site_name'],
                                         name, sel, soup)
                            return
            else:
                details_text = details_text + detail_content

        if details_text:
            details = {}
            for detail_name, detail_config in selector['details'].items():
                detail_value = self.get_detail_value(details_text, detail_config)
                if not detail_value:
                    entry.fail('Details=> detail: {} not found.'.format(detail_name))
                    logger.error('Details=> site: {}, regex: {}，details_text: {}', entry['site_name'],
                                 detail_config['regex'], details_text)
                    return
                details[detail_name] = detail_value
            entry['details'] = details
            logger.info('site_name: {}, details: {}', entry['site_name'], entry['details'])
        else:
            entry.fail('Details=> details_text is None.')

    def check_net_state(self, entry, response, original_url):
        if not response:
            entry.fail(
                entry['prefix'] + '=> ' + SignState.NETWORK_ERROR.value.format(url=original_url,
                                                                               error='Response is None'))
            return SignState.NETWORK_ERROR

        if response.url != original_url:
            entry.fail(entry['prefix'] + '=> ' + SignState.URL_REDIRECT.value.format(original_url, response.url))
            return SignState.URL_REDIRECT

    def check_sign_in_state(self, entry, response, original_url, regex=None):
        net_state = self.check_net_state(entry, response, original_url)
        if net_state:
            return net_state, None

        content = self._decode(response)

        succeed_regex = regex if regex else entry.get('succeed_regex')
        if not succeed_regex:
            entry['result'] = SignState.SUCCEED.value
            return SignState.SUCCEED, content

        succeed_msg = re.search(succeed_regex, content)
        if succeed_msg:
            entry['result'] = re.sub('<.*?>', '', succeed_msg.group())
            return SignState.SUCCEED, content

        wrong_regex = entry.get('wrong_regex')
        if wrong_regex and re.search(wrong_regex, content):
            return SignState.WRONG_ANSWER, content

        return SignState.NO_SIGN_IN, content

    def final_check(self, entry, response, original_url):
        sign_in_state, content = self.check_sign_in_state(entry, response, original_url)
        if sign_in_state == SignState.NO_SIGN_IN:
            entry.fail(SignState.SIGN_IN_FAILED.value.format('no sign in'))
            return SignState.SIGN_IN_FAILED
        return sign_in_state

    def _decode(self, response):
        content = response.content
        content_encoding = response.headers.get('content-encoding')
        if content_encoding == 'br':
            content = brotli.decompress(content)
        charset_encoding = chardet.detect(content).get('encoding')
        if charset_encoding == 'ascii':
            charset_encoding = 'unicode_escape'
        elif charset_encoding == 'Windows-1254':
            charset_encoding = 'utf-8'
        return content.decode(charset_encoding if charset_encoding else 'utf-8', 'ignore')

    def _dict_merge(self, dict1, dict2):
        for i in dict2:
            if isinstance(dict1.get(i), dict) and isinstance(dict2.get(i), dict):
                self._dict_merge(dict1[i], dict2[i])
            else:
                dict1[i] = dict2[i]

    def is_url(self, instance):
        regexp = (
                '('
                + '|'.join(['ftp', 'http', 'https', 'file', 'udp', 'socks5h?'])
                + r'):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'
        )
        return re.match(regexp, instance)

    def get_detail_value(self, content, detail_config):
        if detail_config is None:
            return '*'
        detail_match = re.search(detail_config['regex'], content, re.DOTALL)
        if not detail_match:
            return None
        detail = detail_match.group(detail_config.get('group_index', 1))
        if not detail:
            return None
        detail = detail.replace(',', '')
        handle = detail_config.get('handle')
        if handle:
            detail = handle(detail)
        return detail

    def selenium_get_cookie(self, command_executor, headers):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('user-agent=' + headers['user-agent'])
        driver = webdriver.Remote(command_executor=command_executor,
                                  desired_capabilities=DesiredCapabilities.CHROME,
                                  options=options)
        driver.get(headers['referer'])
        for i in headers['cookie'].split(';'):
            key, value, = i.split('=')
            key = key.strip()
            if key not in ['__cfduid', 'cf_clearance']:
                driver.add_cookie({'name': key.strip(), 'value': value.strip()})

        time.sleep(5)

        receive_cookie = ''
        for c in driver.get_cookies():
            receive_cookie += '{}={}; '.format(c['name'], c['value'])

        driver.quit()

        return receive_cookie.strip()

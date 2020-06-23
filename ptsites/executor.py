import importlib
import itertools
import json
import os
import re
import time
from enum import Enum
from pathlib import Path
from urllib.parse import urljoin
from . import sites

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
    NETWORK_ERROR = 'Network error: {}'
    SIGN_IN_FAILED = 'Sign in failed, {}'


class Executor:

    def __init__(self):
        self.requests = None

    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        entry['url'] = site_config.get('url', '')
        cookie = site_config.get('cookie')
        user_agent = config.get('user-agent')
        entry['base_url'] = site_config.get('base_url')
        referer = site_config.get('base_url', entry['url'])
        headers = {
            'cookie': cookie,
            'user-agent': user_agent,
            'referer': referer
        }
        if brotli:
            headers['accept-encoding'] = 'gzip, deflate, br'
        entry['headers'] = headers
        entry['data'] = site_config.get('data')
        entry['get_message'] = site_config.get('get_message', 'NexusPHP')
        entry['message_url'] = site_config.get('message_url')
        entry['method'] = site_config.get('method', 'get')

        entry['aipocr'] = config.get('aipocr')
        entry['command_executor'] = config.get('command_executor')

        entry['result'] = ''
        entry['messages'] = ''

    def do_sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_nexusphp_message(entry, config)

    @staticmethod
    def execute_build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        if isinstance(site_config, str) or not site_config.get('url'):
            try:
                site_module = getattr(sites, site_name.lower())
                site_class = getattr(site_module, 'MainClass')
                site_class.build_sign_in_entry(entry, site_name, config)
                entry['site_class'] = site_class
            except AttributeError as e:
                raise plugin.PluginError(str(e.args))
        else:
            Executor.build_sign_in_entry(entry, site_name, config)

    def execute_sign_in(self, entry, config):
        # command_executor = config.get('command_executor')
        # cf = entry['site_config'].get('cf')
        # if cf:
        #     if command_executor and webdriver:
        #         try:
        #             cookie = self.selenium_get_cookie(command_executor, entry['headers'])
        #         except Exception as e:
        #             entry['result'] = str(e)
        #             entry.fail(entry['result'])
        #             return
        #     else:
        #         entry['result'] = 'command_executor or webdriver not existed'
        #         entry.fail(entry['result'])
        #         return
        #     entry['headers']['cookie'] = cookie

        site_class = entry.get('site_class')
        if site_class:
            site_object = site_class()
            site_object.do_sign_in(entry, config)
            site_object.get_message(entry, config)
        else:
            method = entry.get('method')
            if method == 'get':
                self.sign_in_by_get(entry, config)
            elif method in ['post', 'post_form']:
                self.sign_in_by_post_data(entry, config)
            elif method == 'question':
                self.sign_in_by_question(entry, config)
            else:
                entry['result'] = 'No method named: {}'.format(method)
                entry.fail(entry['result'])
                return

            if str(entry['get_message']).lower() == 'nexusphp':
                self.get_nexusphp_message(entry, config)
            elif str(entry['get_message']).lower() == 'gazelle':
                self.get_gazelle_message(entry, config)
        logger.info('{} {}\n{}'.format(entry['title'], entry['result'], entry['messages']).strip())

    def _request(self, entry, method, url, is_message=False, **kwargs):
        if not self.requests:
            self.requests = requests.Session()
            headers = kwargs.get('headers')
            if headers:
                if brotli:
                    headers['accept-encoding'] = 'gzip, deflate, br'
                self.requests.headers = headers
            self.requests.mount('http://', HTTPAdapter(max_retries=2))
            self.requests.mount('https://', HTTPAdapter(max_retries=2))
        try:
            response = self.requests.request(method, url, allow_redirects=False, timeout=60, **kwargs)
            if response.status_code == 302:
                redirect_url = urljoin(url, response.headers['Location'])
                response = self._request(entry, method, redirect_url, **kwargs)
            return response
        except Exception as e:
            if not is_message:
                entry['result'] = SignState.NETWORK_ERROR.value.format(str(e.args))
        return None

    def sign_in_by_get(self, entry, config):
        response = self._request(entry, 'get', entry['url'], headers=entry['headers'])
        self.final_check(entry, response, entry['url'])

    def sign_in_by_post_data(self, entry, config):
        base_response = self._request(entry, 'get', entry['base_url'], headers=entry['headers'])
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
                    entry['result'] = 'Cannot find key: {}, url: {}'.format(key, entry['url'])
                    entry.fail(entry['result'])
                    return
        if entry.get('method') == 'post_form':
            response = self._request(entry, 'post', entry['url'], files=data)
        else:
            response = self._request(entry, 'post', entry['url'], data=data)
        self.final_check(entry, response, entry['url'])

    def sign_in_by_question(self, entry, config):
        base_response = self._request(entry, 'get', entry['url'], headers=entry['headers'])
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
        entry['result'] = SignState.SIGN_IN_FAILED.value.format('No answer')
        entry.fail(entry['result'])

    def get_nexusphp_message(self, entry, config):
        message_url = entry.get('message_url') if entry.get('message_url') else urljoin(entry['url'], '/messages.php')
        message_box_response = self._request(entry, 'get', message_url, is_message=True)
        net_state = self.check_net_state(entry, message_box_response, message_url, is_message=True)
        if net_state:
            entry['messages'] = 'Can not read message box!'
            entry.fail(entry['messages'])
            return

        unread_elements = get_soup(self._decode(message_box_response)).select(
            'td > img[alt*="Unread"]')
        failed = False
        for unread_element in unread_elements:
            td = unread_element.parent.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url, is_message=True)
            net_state = self.check_net_state(entry, message_response, message_url, is_message=True)
            if net_state:
                message_body = 'Can not read message body!'
                failed = True
            else:
                body_element = get_soup(self._decode(message_response)).select_one('td[colspan*="2"]')
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        if failed:
            entry.fail('Can not read message body!')

    def get_gazelle_message(self, entry, config):
        message_url = urljoin(entry['url'], '/inbox.php')
        message_box_response = self._request(entry, 'get', message_url, is_message=True)
        net_state = self.check_net_state(entry, message_box_response, message_url, is_message=True)
        if net_state:
            entry['messages'] = 'Can not read message box!'
            entry.fail(entry['messages'])
            return
        unread_elements = get_soup(self._decode(message_box_response)).select("tr.unreadpm > td > strong > a")
        failed = False
        for unread_element in unread_elements:
            title = unread_element.text
            href = unread_element.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url, is_message=True)
            net_state = self.check_net_state(entry, message_response, message_url, is_message=True)
            if net_state:
                message_body = 'Can not read message body!'
                failed = True
            else:
                body_element = get_soup(
                    self._decode(message_response)).select_one('div[id*="message"]')
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        if failed:
            entry.fail('Can not read message body!')

    def check_net_state(self, entry, response, original_url, is_message=False):
        if not response:
            if not is_message:
                if not entry['result'] and not is_message:
                    entry['result'] = SignState.NETWORK_ERROR.value.format('Response is None')
                entry.fail(entry['result'])
            return SignState.NETWORK_ERROR

        if response.url != original_url:
            if not is_message:
                entry['result'] = SignState.URL_REDIRECT.value.format(original_url, response.url)
                entry.fail(entry['result'])
            return SignState.URL_REDIRECT

    def check_sign_in_state(self, entry, response, original_url):
        net_state = self.check_net_state(entry, response, original_url)
        if net_state:
            return net_state, None

        content = self._decode(response)

        succeed_regex = entry.get('succeed_regex')
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
        if sign_in_state in [SignState.NETWORK_ERROR, SignState.URL_REDIRECT]:
            return
        elif sign_in_state == SignState.NO_SIGN_IN:
            entry['result'] = SignState.SIGN_IN_FAILED
            entry.fail(entry['result'])
            logger.warning(content)

    def _decode(self, response):
        content = response.content
        content_encoding = response.headers.get('content-encoding')
        if content_encoding == 'br':
            content = brotli.decompress(content)
        charset_encoding = chardet.detect(content).get('encoding')
        if charset_encoding == 'ascii':
            charset_encoding = 'unicode_escape'
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

    @staticmethod
    def execute_build_reseed_entry(entry, base_url, site, site_name, passkey, torrent_id):
        try:
            site_module = importlib.import_module('ptsites.sites.{}'.format(site_name.lower()))
            site_class = getattr(site_module, 'MainClass')
            site_class.build_reseed_entry(entry, base_url, site, passkey, torrent_id)
        except ModuleNotFoundError as e:
            Executor.build_reseed_entry(entry, base_url, site, passkey, torrent_id)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id + '&passkey=' + passkey)
        entry['url'] = 'https://{}/{}'.format(base_url, download_page)

import gzip
import itertools
import json
import os
import re
from datetime import datetime
from enum import Enum
from os import path
from pathlib import Path
from urllib.parse import urljoin

import chardet
from flexget import plugin, config_schema
from flexget.entry import Entry
from flexget.event import event
from flexget.utils.soup import get_soup
from loguru import logger

try:
    import brotli
except ImportError:
    brotli = None


class SignState(Enum):
    NO_SIGN_IN = 'No sign in'
    SUCCEED = 'Succeed'
    WRONG_ANSWER = 'Wrong answer'
    URL_REDIRECT = 'Url: {} redirect to {}'
    UNKNOWN = 'Unknown, url: {}'
    NETWORK_ERROR = 'Network error: {}'
    SIGN_IN_FAILED = 'Sign in failed, url: {}'


class PluginAutoSignIn:
    schema = {
        'type': 'object',
        'properties': {
            'user-agent': {'type': 'string'},
            'sites': {
                'type': 'object',
                'properties': {
                }
            }
        },
        'additionalProperties': False
    }

    def prepare_config(self, config):
        config.setdefault('user-agent', '')
        config.setdefault('sites', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        sites = config.get('sites')
        user_agent = config.get('user-agent')

        entries = []

        for site_name, site_config in sites.items():
            entry = Entry(
                title='{} {}'.format(site_name, datetime.now().date()),
                url=site_config.get('url', ''),
            )
            cookie = site_config.get('cookie')

            entry['site_config'] = site_config
            entry['base_url'] = site_config.get('base_url')
            headers = {
                'cookie': cookie,
                'user-agent': user_agent,
                'referer': site_config.get('base_url', entry['url']),
            }
            if brotli:
                headers['accept-encoding'] = 'gzip, deflate, br'
            entry['headers'] = headers
            entry['data'] = site_config.get('data')
            entry['result'] = ''
            entry['get_message'] = site_config.get('get_message', 'NexusPHP')
            entry['message_url'] = site_config.get('message_url')
            entry['messages'] = ''
            entry['cookie'] = cookie
            entry['method'] = site_config.get('method', 'get')
            entries.append(entry)
        return entries

    def on_task_output(self, task, config):
        for entry in task.accepted:

            if not entry['cookie']:
                entry['result'] = 'Manual url: {}'.format(entry['url'])
                continue

            method = entry['method']
            if method == 'post':
                self.sign_in_by_post_data(task, entry)
            elif method == 'question':
                self.sign_in_by_question(task, entry)
            else:
                self.sign_in_by_get(task, entry)

            if str(entry['get_message']).lower() == 'nexusphp':
                self.get_nexusphp_message(task, entry)
            elif str(entry['get_message']).lower() == 'gazelle':
                self.get_gazelle_message(task, entry)

            logger.info('{} {}\n{}'.format(entry['title'], entry['result'], entry['messages']).strip())

    def _request(self, task, entry, method, url, **kwargs):
        try:
            return task.requests.request(method, url, **kwargs)
        except Exception as e:
            if url in [entry['url'], entry['base_url']]:
                entry['result'] = SignState.NETWORK_ERROR.value.format(str(e))
            else:
                entry['messages'] = SignState.NETWORK_ERROR.value.format(str(e))
        return None

    def sign_in_by_get(self, task, entry):
        response = self._request(task, entry, 'get', entry['url'], headers=entry['headers'])
        self.check_state(entry, response, entry['url'])

    def sign_in_by_post_data(self, task, entry):
        response = self._request(task, entry, 'get', entry['base_url'], headers=entry['headers'])
        state = self.check_state(entry, response, entry['base_url'])
        if state != SignState.NO_SIGN_IN:
            return
        content = self._decode(response)
        data = {}
        for key, regex in entry.get('data', {}).items():
            value_search = re.search(regex, content)
            if value_search:
                data[key] = value_search.group()
            else:
                entry['result'] = 'Cannot find key: {}, url: {}'.format(key, entry['url'])
                entry.fail(entry['result'])
                return
        response = self._request(task, entry, 'post', entry['url'], headers=entry['headers'], data=data)
        self.check_state(entry, response, entry['url'])

    def sign_in_by_question(self, task, entry):
        response = self._request(task, entry, 'get', entry['url'], headers=entry['headers'])
        state = self.check_state(entry, response, entry['url'])
        if state != SignState.NO_SIGN_IN:
            return

        content = self._decode(response)
        question_element = get_soup(content).select_one('input[name="questionid"]')
        if question_element:
            question_id = question_element.get('value')

            local_answer = None

            question_file_path = path.dirname(__file__) + '/question.json'
            if Path(question_file_path).is_file():
                with open(question_file_path) as question_file:
                    question_json = json.loads(question_file.read())
            else:
                question_json = {}

            question_extend_file_path = path.dirname(__file__) + '/question_extend.json'
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

            choice_elements = get_soup(content).select('input[name="choice[]"]')
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
                response = self._request(task, entry, 'post', entry['url'], headers=entry['headers'], data=data)
                state = self.check_state(entry, response, entry['url'])
                if state == SignState.SUCCEED:
                    entry['result'] = '{} ( {} attempts.)'.format(entry['result'], times)

                    question_json[entry['url']][question_id] = answer
                    with open(question_file_path, mode='w') as question_file:
                        json.dump(question_json, question_file)
                    logger.info('{}, correct answer: {}', entry['title'], data)
                    return
                times += 1
        entry['result'] = 'no answer'
        entry.fail(entry['result'])

    def get_nexusphp_message(self, task, entry):
        message_url = entry['message_url'] if entry['message_url'] else urljoin(entry['url'], '/messages.php')
        message_box_response = self._request(task, entry, 'get', message_url, headers=entry['headers'])
        if message_box_response:
            unread_elements = get_soup(self._decode(message_box_response)).select(
                'td > img[alt*="Unread"]')
            for unread_element in unread_elements:
                td = unread_element.parent.nextSibling.nextSibling
                title = td.text
                href = td.a.get('href')
                message_url = urljoin(message_url, href)
                message_response = self._request(task, entry, 'get', message_url, headers=entry['headers'])

                message_body = 'Can not read message body!'
                if message_response:
                    body_element = get_soup(
                        self._decode(message_response)).select_one('td[colspan*="2"]')
                    if body_element:
                        message_body = body_element.text.strip()

                entry['messages'] = entry['messages'] + (
                    '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        else:
            entry['messages'] = 'Can not read message box!'

    def get_gazelle_message(self, task, entry):
        message_url = urljoin(entry['url'], '/inbox.php')
        message_box_response = self._request(task, entry, 'get', message_url, headers=entry['headers'])
        if message_box_response:
            unread_elements = get_soup(self._decode(message_box_response)).select(
                "tr.unreadpm > td > strong > a")
            for unread_element in unread_elements:
                title = unread_element.text
                href = unread_element.get('href')
                message_url = urljoin(message_url, href)
                message_response = self._request(task, entry, 'get', message_url, headers=entry['headers'])

                message_body = 'Can not read message body!'
                if message_response:
                    body_element = get_soup(
                        self._decode(message_response)).select_one('div[id*="message"]')
                    if body_element:
                        message_body = body_element.text.strip()

                entry['messages'] = entry['messages'] + (
                    '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        else:
            entry['messages'] = 'Can not read message box!'

    def check_state(self, entry, response, original_url):
        if not response:
            if not entry['result']:
                entry['result'] = SignState.NETWORK_ERROR.value.format(response)
            entry.fail(entry['result'])
            return SignState.NETWORK_ERROR

        if original_url != response.url:
            entry['result'] = SignState.URL_REDIRECT.value.format(original_url, response.url)
            entry.fail(entry['result'])
            return SignState.URL_REDIRECT

        content = self._decode(response)

        succeed_regex = entry['site_config'].get('succeed_regex')
        if not succeed_regex:
            entry['result'] = SignState.SUCCEED.value
            return SignState.SUCCEED

        succeed_msg = re.search(succeed_regex, content)
        if succeed_msg:
            entry['result'] = re.sub('<.*?>', '', succeed_msg.group())
            return SignState.SUCCEED

        wrong_regex = entry['site_config'].get('wrong_regex')
        if wrong_regex and re.search(wrong_regex, content):
            return SignState.WRONG_ANSWER

        if entry['method'] == 'get':
            entry['result'] = SignState.SIGN_IN_FAILED.value.format(original_url)
            entry.fail(entry['result'])
            return SignState.SIGN_IN_FAILED
        return SignState.NO_SIGN_IN

    def _decode(self, response):
        content = response.content
        content_encoding = response.headers.get('content-encoding')
        if content_encoding == 'br':
            content = brotli.decompress(content)
        charset_encoding = chardet.detect(content).get('encoding')
        if charset_encoding == 'ascii':
            charset_encoding = 'unicode_escape'
        return content.decode(charset_encoding, 'ignore')

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


@event('plugin.register')
def register_plugin():
    plugin.register(PluginAutoSignIn, 'auto_sign_in', api_ver=2)

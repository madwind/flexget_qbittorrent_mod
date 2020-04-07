import gzip
import itertools
import json
import re
from datetime import datetime
from enum import Enum
from os import path
from pathlib import Path

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.utils.soup import get_soup
from loguru import logger
from requests import RequestException


class SignState(Enum):
    NO_SIGN_IN = 'No sign in'
    SUCCEED = 'Succeed'
    WRONG_ANSWER = 'Wrong answer'
    URL_REDIRECT = 'Url: {} redirect to {}'
    UNKNOWN = 'Unknown, url: {}'
    NETWORK_ERROR = 'Network error, msg: {}, url: {}'
    SIGN_IN_FAILED = 'Sign in failed, url: {}'


class PluginAutoSignIn():
    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
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
        ]
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
                title='{} {}'.format(datetime.now().date(), site_name),
                url=site_config.get('url', ''),
            )
            cookie = site_config.get('cookie')

            entry['site_config'] = site_config
            entry['base_url'] = site_config.get('base_url')
            headers = {'cookie': cookie, 'user-agent': user_agent,
                       'referer': site_config.get('base_url', entry['url'])}
            entry['headers'] = headers
            entry['data'] = site_config.get('data')
            entry['encoding'] = site_config.get('encoding', 'utf-8')
            entry['message'] = ''
            entry['cookie'] = cookie
            entry['method'] = site_config.get('method', 'get')
            entries.append(entry)

        return entries

    def on_task_output(self, task, config):
        for entry in task.accepted:
            logger.info(entry['title'])
            method = entry['method']

            if not entry['cookie']:
                entry['message'] = 'Manual url: {}'.format(entry['url'])
                continue

            if method == 'post':
                self.sign_in_by_post_data(task, entry)
            elif method == 'question':
                self.sign_in_by_question(task, entry)
            else:
                self.sign_in_by_get(task, entry)

    def _request(self, task, entry, method, url, **kwargs):
        try:
            response = task.requests.request(method, url, **kwargs)
            return response
        except RequestException as e:
            entry['message'] = SignState.NETWORK_ERROR.value.format(str(e), url)

    def sign_in_by_get(self, task, entry):
        response = self._request(task, entry, 'get', entry['url'], headers=entry['headers'])
        self.check_state(entry, response, entry['url'])

    def sign_in_by_post_data(self, task, entry):
        response = self._request(task, entry, 'get', entry['base_url'], headers=entry['headers'])
        state = self.check_state(entry, response, entry['base_url'])
        if state != SignState.NO_SIGN_IN:
            return
        content = self.decode(response.content, entry['encoding'])
        data = {}
        for key, regex in entry.get('data', {}).items():
            value_search = re.search(regex, content)
            if value_search:
                data[key] = value_search.group()
            else:
                entry['message'] = 'Cannot find key: {}, url: {}'.format(key, entry['url'])
                entry.fail(entry['message'])
                return
        response = self._request(task, entry, 'post', entry['url'], headers=entry['headers'], data=data)
        self.check_state(entry, response, entry['url'])

    def sign_in_by_question(self, task, entry):
        response = self._request(task, entry, 'get', entry['url'], headers=entry['headers'])
        state = self.check_state(entry, response, entry['url'])
        if state != SignState.NO_SIGN_IN:
            return

        content = self.decode(response.content, entry['encoding'])
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

            for answer in answer_list:
                data = {'questionid': question_id, 'choice[]': answer, 'usercomment': '此刻心情:无', 'submit': '提交'}
                response = self._request(task, entry, 'post', entry['url'], headers=entry['headers'], data=data)
                state = self.check_state(entry, response, entry['url'])
                if state == SignState.SUCCEED:
                    question_json[entry['url']][question_id] = answer
                    with open(question_file_path, mode='w') as question_file:
                        json.dump(question_json, question_file)
                    logger.info('{}, correct answer: {}', entry['title'], data)
                    return
        entry['message'] = 'no answer'
        entry.fail(entry['message'])

    def check_state(self, entry, response, original_url):
        if not response:
            if not entry['message']:
                entry['message'] = SignState.NETWORK_ERROR.value.format(response, original_url)
            entry.fail(entry['message'])
            return SignState.NETWORK_ERROR

        if original_url != response.url:
            entry['message'] = SignState.URL_REDIRECT.value.format(original_url, response.url)
            entry.fail(entry['message'])
            return SignState.URL_REDIRECT

        content = self.decode(response.content, (entry['encoding']))

        succeed_regex = entry['site_config'].get('succeed_regex')
        if not succeed_regex:
            entry['message'] = SignState.SUCCEED
            return SignState.SUCCEED

        succeed_msg = re.search(succeed_regex, content)
        if succeed_msg:
            entry['message'] = re.sub('<.*?>', '', succeed_msg.group())
            return SignState.SUCCEED

        wrong_regex = entry['site_config'].get('wrong_regex')
        if wrong_regex and re.search(wrong_regex, content):
            return SignState.WRONG_ANSWER

        if entry['method'] == 'get':
            entry['message'] = SignState.SIGN_IN_FAILED.value.format(original_url)
            entry.fail(entry['message'])
            return SignState.SIGN_IN_FAILED
        return SignState.NO_SIGN_IN

    def decode(self, content, encoding):
        try:
            html = content.decode(encoding)
        except UnicodeDecodeError:
            html = gzip.decompress(content).decode(encoding)
        return html


@event('plugin.register')
def register_plugin():
    plugin.register(PluginAutoSignIn, 'auto_sign_in', api_ver=2)

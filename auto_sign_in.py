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
    NO_SIGN_IN = 'no_sign_in'
    SUCCEED = 'succeed'
    WRONG_ANSWER = 'wrong_answer'
    UNKNOWN = 'unknown'


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
                       'referer': entry['base_url'] if entry['base_url'] else entry['url']}
            entry['headers'] = headers
            entry['data'] = site_config.get('data')
            entry['encode'] = site_config.get('data') if site_config.get('data') else 'utf-8'
            entry['message'] = ''
            entries.append(entry)

        return entries

    def on_task_output(self, task, config):
        for entry in task.accepted:
            logger.info('url: {}', entry['url'])
            site_config = entry.get('site_config')
            method = site_config.get('method')

            if method == 'post':
                self.post_data_sign_in(task, entry)
            elif method == 'question':
                self.question_sign_in(task, entry)
            else:
                self.get_sign_in(task, entry)

    def get_sign_in(self, task, entry):
        try:
            response = task.requests.get(entry['url'], headers=entry['headers'])
            logger.debug('response: {}', response.content.decode(entry['encode']))
            self.check_state(entry, response, entry['url'])
        except RequestException as e:
            entry.fail()
            entry['message'] = 'Network error. {}'.format(entry['url'])
            logger.error('Unable to sign in for task {} ({}): {}'.format(task.name, entry['url'], e))

    def post_data_sign_in(self, task, entry):
        response = self.get_sign_in_page(task, entry)
        if not response:
            return
        content = response.content
        data = {}
        for key, regex in entry.get('data', {}).items():
            data[key] = re.search(regex, content.decode(entry['encode'])).group()
        self.post_sign_in(task, entry, data)

    def question_sign_in(self, task, entry):
        response = self.get_sign_in_page(task, entry)
        if not response:
            return
        content = response.content
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
            if local_answer and local_answer in choices and len(local_answer) <= choice_range:
                answer_list.append(local_answer)

            for i in range(choice_range):
                for arr in itertools.combinations(choices, i + 1):
                    if list(arr) not in answer_list:
                        answer_list.append(list(arr))
            for answer in answer_list:
                data = {'questionid': question_id, 'choice[]': answer, 'usercomment': '此刻心情:无', 'submit': '提交'}
                logger.info('url: {}, trying answer: {}', entry['url'], data)
                state = self.post_sign_in(task, entry, data)
                if not state:
                    return
                if state == SignState.SUCCEED:
                    question_json[entry['url']][question_id] = answer
                    with open(question_file_path, mode='w') as question_file:
                        json.dump(question_json, question_file)
                    logger.info('url: {}, correct answer: {}', entry['url'], data)
                    return
            entry['message'] = 'no answer'
            entry.fail()

    def get_sign_in_page(self, task, entry):
        url = entry['base_url'] if entry['base_url'] else entry['url']
        response = task.requests.get(url, headers=entry['headers'])
        state = self.check_state(entry, response, url)
        if state == SignState.UNKNOWN:
            return None
        elif state == SignState.SUCCEED:
            return None
        return response

    def post_sign_in(self, task, entry, data):
        try:
            response = task.requests.post(entry['url'], headers=entry['headers'], data=data)
            logger.debug('response: {}, data: {}', response.content.decode(entry['encode']), data)
            return self.check_state(entry, response, entry['url'])
        except RequestException as e:
            entry.fail()
            entry['message'] = 'Network error. {}'.format(entry['url'])
            logger.error('Unable to sign in for task {} ({}): {}'.format(task.name, entry['url'], e))
        return None

    def check_state(self, entry, response, url):
        encode = entry['encode']
        if url != response.url:
            logger.info('{} failed: {}', entry['title'], url)
            entry['message'] = 'failed. {}'.format(url)
            entry.fail()
            return SignState.UNKNOWN

        succeed_regex = entry['site_config'].get('succeed_regex')

        if not succeed_regex:
            entry['message'] = SignState.SUCCEED
            return SignState.SUCCEED

        succeed_msg = re.search(succeed_regex, response.content.decode(encode))
        if succeed_msg:
            entry['message'] = re.sub('<.*?>', '', succeed_msg.group())
            return SignState.SUCCEED

        wrong_regex = entry['site_config'].get('wrong_regex')
        if wrong_regex and re.search(wrong_regex, response.content.decode(encode)):
            return SignState.WRONG_ANSWER

        return SignState.NO_SIGN_IN


@event('plugin.register')
def register_plugin():
    plugin.register(PluginAutoSignIn, 'auto_sign_in', api_ver=2)

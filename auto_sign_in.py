import re
from datetime import datetime
from enum import Enum

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
            entry['message'] = ''
            entries.append(entry)

        return entries

    def on_task_output(self, task, config):
        for entry in task.accepted:
            logger.info('sign_in for {}', entry['url'])
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
            self.check_state(entry, response, entry['url'])
        except RequestException as e:
            entry.fail()
            entry['message'] = 'Network error'
            logger.error('Unable to sign in for task {} ({}): {}'.format(task.name, entry['url'], e))

    def post_data_sign_in(self, task, entry):
        response = self.get_sign_in_page(task, entry)
        if not response:
            return
        content = response.content
        data = {}
        for key, regex in entry.get('data', {}).items():
            data[key] = re.search(regex, content.decode()).group()
        self.post_sign_in(task, entry, data)

    def question_sign_in(self, task, entry):
        response = self.get_sign_in_page(task, entry)
        if not response:
            return
        content = response.content
        question_element = get_soup(content).select_one('input[name="questionid"]')
        if question_element:
            question_id = question_element.get('value')
            choice_elements = get_soup(content).select('input[name="choice[]"]')
            choice_all = []
            for choice_element in choice_elements:
                choice_all.append(choice_element.get('value', ''))
            if choice_elements[0].get('type') == 'radio':
                choice_all = sorted(choice_all)
                for choice_index in choice_all:
                    data = {'questionid': question_id, 'choice[]': [choice_index],
                            'usercomment': '此刻心情:无', 'submit': '提交'}
                    logger.info('trying sign_in url{}, data: {}', entry['url'], data)
                    state = self.post_sign_in(task, entry, data)
                    if not state:
                        return
                    if state == SignState.SUCCEED:
                        logger.info('succeed: sign_in url{}, data: {}', entry['url'], data)
                        return
                entry['message'] = 'no answer'
                entry.fail()
            else:
                data = {'questionid': question_id, 'choice[]': choice_all, 'usercomment': '此刻心情:无',
                        'wantskip': '不会'}
                logger.info('trying sign_in url{}, data: {}', entry['url'], data)
                state = self.post_sign_in(task, entry, data)
                if not state:
                    return
                if state == SignState.SUCCEED:
                    logger.info('succeed: sign_in url{}, data: {}', entry['url'], data)
                else:
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
            logger.info('response: {}, data: {}', data, response.content.decode())
            return self.check_state(entry, response, entry['url'])
        except RequestException as e:
            entry.fail()
            entry['message'] = 'Network error'
            logger.error('Unable to sign in for task {} ({}): {}'.format(task.name, entry['url'], e))
        return None

    def check_state(self, entry, response, url):
        if url != response.url:
            logger.info('{} failed: {}', entry['title'], url)
            entry['message'] = 'failed. {}'.format(url)
            entry.fail()
            return SignState.UNKNOWN

        succeed_regex = entry['site_config'].get('succeed_regex')

        if not succeed_regex:
            entry['message'] = SignState.SUCCEED
            return SignState.SUCCEED

        succeed_msg = re.search(succeed_regex, response.content.decode())
        if succeed_msg:
            entry['message'] = succeed_msg.group()
            return SignState.SUCCEED

        wrong_regex = entry['site_config'].get('wrong_regex')
        if wrong_regex and re.search(wrong_regex, response.content.decode()):
            return SignState.WRONG_ANSWER

        return SignState.NO_SIGN_IN


@event('plugin.register')
def register_plugin():
    plugin.register(PluginAutoSignIn, 'auto_sign_in', api_ver=2)

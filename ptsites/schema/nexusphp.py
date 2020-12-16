import itertools
import json
from pathlib import Path
from urllib.parse import urljoin

from flexget.utils.soup import get_soup
from loguru import logger

from .site_base import SiteBase, SignState


class NexusPHP(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_nexusphp_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'user_id': 'userdetails.php\\?id=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(1) > span',
                        'table': '#outer table:last-child'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': ('(上[传傳]量|Uploaded).+?([\\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'downloaded': {
                    'regex': ('(下[载載]量|Downloaded).+?([\\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'share_ratio': {
                    'regex': ('(分享率|Ratio).*?(---|∞|Inf\\.|无限|無限|[\\d.]+)', 2),
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': ('(魔力|Bonus).*?([\\d,.]+)', 2)
                },
                'seeding': {
                    'regex': ('(当前活动|當前活動).*?(\\d+)', 2)
                },
                'leeching': {
                    'regex': ('(当前活动|當前活動).*?\\d+\\D+(\\d+)', 2)
                },
                'hr': {
                    'regex': 'H&R.*?(\\d+)'
                }
            }
        }
        return selector

    def get_nexusphp_message(self, entry, config, messages_url='/messages.php'):
        message_url = urljoin(entry['url'], messages_url)
        message_box_response = self._request(entry, 'get', message_url)
        net_state = self.check_net_state(entry, message_box_response, message_url)
        if net_state:
            entry.fail_with_prefix('Can not read message box! url:{}'.format(message_url))
            return

        unread_elements = get_soup(self._decode(message_box_response)).select(
            'td > img[alt*="Unread"]')
        failed = False
        for unread_element in unread_elements:
            td = unread_element.parent.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url)
            net_state = self.check_net_state(entry, message_response, message_url)
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
            entry.fail_with_prefix('Can not read message body!')

    def sign_in_by_question(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', entry['url'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, entry['url'])
        if sign_in_state != SignState.NO_SIGN_IN:
            return

        question_element = get_soup(base_content).select_one('input[name="questionid"]')
        if question_element:
            question_id = question_element.get('value')

            local_answer = None
            question_file = Path.cwd().joinpath('nexusphp_question.json')
            if question_file.is_file():
                question_json = json.loads(question_file.read_text())
            else:
                question_json = {}

            question_extend_file = Path(__file__).with_name('nexusphp_question.json')
            if question_extend_file.is_file():
                question_extend_json = json.loads(question_extend_file.read_text())
                self.dict_merge(question_json, question_extend_json)
                question_file.write_text(json.dumps(question_json))
                question_extend_file.unlink()

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
                    question_file.write_text(json.dumps(question_json))
                    logger.info('{}, correct answer: {}', entry['title'], data)
                    return
                times += 1
        entry.fail_with_prefix(SignState.SIGN_IN_FAILED.value.format('No answer.'))

    def handle_share_ratio(self, value):
        if value in ['---', '∞', 'Inf.', '无限', '無限']:
            return '0'
        else:
            return value

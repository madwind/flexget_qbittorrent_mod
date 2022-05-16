import itertools
import json
import re
from pathlib import Path
from urllib.parse import urljoin

from flexget.utils.soup import get_soup
from loguru import logger

from ..schema.site_base import SiteBase, SignState, NetworkState, Work
from ..utils.net_utils import NetUtils


class NexusPHP(SiteBase):

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
                    'regex': ('(分享率|Ratio).*?(---|∞|Inf\\.|无限|無限|[\\d,.]+)', 2),
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': ('(魔力|Bonus|Bônus).*?([\\d,.]+)', 2)
                },
                'join_date': {
                    'regex': ('(加入日期|注册日期|Join.date|Data de Entrada).*?(\\d{4}-\\d{2}-\\d{2})', 2),
                },
                'seeding': {
                    'regex': ('(当前活动|當前活動|Torrents Ativos).*?(\\d+)', 2)
                },
                'leeching': {
                    'regex': ('(当前活动|當前活動|Torrents Ativos).*?\\d+\\D+(\\d+)', 2)
                },
                'hr': {
                    'regex': 'H&R.*?(\\d+)'
                }
            }
        }
        return selector

    def get_nexusphp_message(self, entry, config, messages_url='/messages.php?action=viewmailbox&box=1&unread=yes',
                             unread_elements_selector='td > img[alt*="Unread"]'):
        message_url = urljoin(entry['url'], messages_url)
        message_box_response = self._request(entry, 'get', message_url)
        message_box_network_state = self.check_network_state(entry, message_url, message_box_response)
        if message_box_network_state != NetworkState.SUCCEED:
            entry.fail_with_prefix('Can not read message box! url:{}'.format(message_url))
            return

        unread_elements = get_soup(NetUtils.decode(message_box_response)).select(
            unread_elements_selector)
        failed = False
        for unread_element in unread_elements:
            td = unread_element.parent.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url)
            message_network_state = self.check_network_state(entry, message_url, message_response)
            if message_network_state != NetworkState.SUCCEED:
                message_body = 'Can not read message body!'
                failed = True
            else:
                if body_element := get_soup(NetUtils.decode(message_response)).select_one('td[colspan*="2"]'):
                    message_body = body_element.text.strip()
                else:
                    message_body = 'Can not find message body element!'
            entry['messages'] = entry['messages'] + (f'\nTitle: {title}\nLink: {message_url}\n{message_body}')
        if failed:
            entry.fail_with_prefix('Can not read message body!')

    def handle_share_ratio(self, value):
        if value in ['---', '∞', 'Inf.', '无限', '無限']:
            return '0'
        else:
            return value


class AttendanceHR(NexusPHP):
    def build_workflow(self, entry, config):
        return [
            Work(
                url='/attendance.php',
                method='get',
                succeed_regex=[
                    '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?魔力值。|這是您的第.*次簽到，已連續簽到.*?天，本次簽到獲得.*?魔力值。',
                    rf'{re.escape("Você já resgatou ")}.*?{re.escape(" dias. Com isso, coletou ")}.*?{re.escape(" dia(s) consecutivos e dessa vez você receberá um bônus de ")}.*?{re.escape(".")}',
                    '[签簽]到已得\\d+',
                    '您今天已经签到过了，请勿重复刷新。|您今天已經簽到過了，請勿重複刷新。'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]


class Attendance(AttendanceHR):
    def build_selector(self):
        selector = super(Attendance, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector


class BakatestHR(NexusPHP):
    def build_workflow(self, entry, config):
        return [
            Work(
                url='/bakatest.php',
                method='get',
                succeed_regex='今天已经签过到了\\(已连续.*天签到\\)',
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/bakatest.php',
                method='question',
                succeed_regex='连续.*天签到,获得.*点魔力值|今天已经签过到了\\(已连续.*天签到\\)',
                fail_regex='回答错误,失去 1 魔力值,这道题还会再考一次',
            )
        ]

    def sign_in_by_question(self, entry, config, work, last_content=None):
        question_element = get_soup(last_content).select_one('input[name="questionid"]')
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
                NetUtils.dict_merge(question_json, question_extend_json)
                question_file.write_text(json.dumps(question_json))
                question_extend_file.unlink()

            site_question = question_json.get(entry['url'])
            if site_question:
                local_answer = site_question.get(question_id)
            else:
                question_json[entry['url']] = {}

            choice_elements = get_soup(last_content).select('input[name="choice[]"]')
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
                response = self._request(entry, 'post', work.url, data=data)
                state = self.check_sign_in_state(entry, work, response, NetUtils.decode(response))
                if state == SignState.SUCCEED:
                    entry['result'] = f"{entry['result']} ( {times} attempts.)"
                    question_json[entry['url']][question_id] = answer
                    question_file.write_text(json.dumps(question_json))
                    logger.info(f"{entry['title']}, correct answer: {data}")
                    return
                times += 1
        entry.fail_with_prefix(SignState.SIGN_IN_FAILED.value.format('No answer.'))


class Bakatest(BakatestHR):

    def build_selector(self):
        selector = super(Bakatest, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector


class VisitHR(NexusPHP):
    SUCCEED_REGEX = '[欢歡]迎回[来來家]'

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=self.SUCCEED_REGEX,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]


class Visit(VisitHR):

    def build_selector(self):
        selector = super(Visit, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

from __future__ import annotations

import itertools
import json
import re
from abc import ABC
from pathlib import Path
from time import sleep
from urllib.parse import urljoin

from flexget.utils.soup import get_soup
from loguru import logger

from .private_torrent import PrivateTorrent
from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import SignState, check_final_state, check_sign_in_state
from ..base.work import Work
from ..utils import net_utils
from ..utils.value_handler import handle_infinite


class NexusPHP(PrivateTorrent, ABC):

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config)

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'userdetails\.php\?id=(\d+)',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'bar': '#info_block',
                        'table': '#outer table.main:last-child'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': (r'(上[传傳]量|Uploaded).+?([\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'downloaded': {
                    'regex': (r'(下[载載]量|Downloaded).+?([\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'share_ratio': {
                    'regex': (r'(分享率|Ratio).*?(---|∞|Inf\.|无限|無限|[\d,.]+)', 2),
                    'handle': handle_infinite
                },
                'points': {
                    'regex': (r'(魔力|Bonus|Bônus).*?([\d,.]+)', 2)
                },
                'join_date': {
                    'regex': (r'(加入日期|注册日期|Join.date|Data de Entrada).*?(\d{4}-\d{2}-\d{2})', 2),
                },
                'seeding': {
                    'regex': (r'(当前活动|當前活動|Torrents Ativos).*?(\d+)', 2)
                },
                'leeching': {
                    'regex': (r'(当前活动|當前活動|Torrents Ativos).*?\d+\D+(\d+)', 2)
                },
                'hr': {
                    'regex': r'H&R.*?(\d+)'
                }
            }
        }

    def get_nexusphp_messages(self, entry: SignInEntry, config: dict,
                              messages_url: str = '/messages.php?action=viewmailbox&box=1&unread=yes',
                              unread_elements_selector: str = 'td > img[alt*="Unread"]',
                              ignore_title: str | None = None) -> None:
        message_url = urljoin(entry['url'], messages_url)
        message_box_response = self.request(entry, 'get', message_url)
        message_box_network_state = check_network_state(entry, message_url, message_box_response)
        if message_box_network_state != NetworkState.SUCCEED:
            entry.fail_with_prefix(f'Can not read message box! url:{message_url}')
            return

        unread_elements = get_soup(net_utils.decode(message_box_response)).select(
            unread_elements_selector)
        failed = False
        for unread_element in unread_elements:
            td = unread_element.parent.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            message_url = urljoin(message_url, href)
            message_response = self.request(entry, 'get', message_url)
            message_network_state = check_network_state(entry, message_url, message_response)
            if message_network_state != NetworkState.SUCCEED:
                message_body = 'Can not read message body!'
                failed = True
            else:
                if body_element := get_soup(net_utils.decode(message_response)).select_one('td[colspan*="2"]'):
                    message_body = body_element.text.strip()
                else:
                    message_body = 'Can not find message body element!'
            if ignore_title and re.match(ignore_title, title):
                logger.info(f'\nIgnore Title: {title}\nLink: {message_url}\n{message_body}')
                continue
            entry['messages'] = entry['messages'] + f'\nTitle: {title}\nLink: {message_url}\n{message_body}'
        if failed:
            entry.fail_with_prefix('Can not read message body!')


class AttendanceHR(NexusPHP, ABC):
    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=[
                    '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?魔力值。|這是您的第.*次簽到，已連續簽到.*?天，本次簽到獲得.*?魔力值。',
                    '[签簽]到已得\\d+',
                    '您今天已经签到过了，请勿重复刷新。|您今天已經簽到過了，請勿重複刷新。'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]


class Attendance(AttendanceHR, ABC):
    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector


class BakatestHR(NexusPHP, ABC):
    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/bakatest.php',
                method=self.sign_in_by_get,
                succeed_regex=['今天已经签过到了\\(已连续.*天签到\\)'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/bakatest.php',
                method=self.sign_in_by_question,
                succeed_regex=['连续.*天签到,获得.*点魔力值|今天已经签过到了\\(已连续.*天签到\\)'],
                fail_regex='回答错误,失去 1 魔力值,这道题还会再考一次',
            )
        ]

    def sign_in_by_question(self, entry: SignInEntry, config: dict, work: Work, last_content: str = None) -> None:
        question_element = get_soup(last_content).select_one('input[name="questionid"]')
        if question_element:
            question_id = question_element.get('value')

            question_file = Path(__file__).parent.parent.joinpath(f'data/{entry["site_name"]}.json')

            if question_file.is_file():
                question_json = json.loads(question_file.read_text(encoding='utf-8'))
            else:
                question_json = {}

            local_answer = question_json.get(question_id)

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
            if local_answer and len(local_answer) == len([i for i in local_answer if i in choices]) and len(
                    local_answer) <= choice_range:
                answer_list.insert(0, local_answer)
            times = 0
            for answer in answer_list:
                data = {'questionid': question_id, 'choice[]': answer, 'usercomment': '此刻心情:无', 'submit': '提交'}
                response = self.request(entry, 'post', work.url, data=data)
                state = check_sign_in_state(entry, work, response, net_utils.decode(response))
                if state == SignState.SUCCEED:
                    entry['result'] = f"{entry['result']} ( {times} attempts.)"
                    if question_json.get(question_id) != answer:
                        question_json[question_id] = answer
                        question_file.write_text(
                            json.dumps({int(x): question_json[x] for x in question_json.keys()}, indent=4),
                            encoding='utf-8')
                    logger.info(f"{entry['title']}, correct answer: {data}")
                    return
                times += 1
                sleep(3)
        entry.fail_with_prefix(SignState.SIGN_IN_FAILED.value.format('No answer.'))


class Bakatest(BakatestHR, ABC):
    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector


class VisitHR(NexusPHP, ABC):
    @property
    def SUCCEED_REGEX(self) -> str:
        return '[欢歡]迎回[来來家]'

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[self.SUCCEED_REGEX],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]


class Visit(VisitHR, ABC):
    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

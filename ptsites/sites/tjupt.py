import re
from typing import Final

import requests
from loguru import logger

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP):
    URL: Final = 'https://tjupt.org/'
    IMG_REGEX: Final = r'https://.*\.doubanio\.com/view/photo/s_ratio_poster/public/(p\d+)\.'
    ANSWER_REGEX: Final = r"<input type='radio' name='answer' value='(.*?)'>(.*?)<br>"
    BREAK_REGEX: Final = r'已断签.*?天，当前可补签天数为 <b>(\d+)</b> 天'
    CONFIRM: Final = {'action': 'confirm'}
    CANCEL: Final = {'action': 'cancel'}
    IGNORE_TITLE = '您正在下载或做种的种子被删除'
    USER_CLASSES: Final = {
        'uploaded': [5368709120000, 53687091200000],
        'days': [336, 924]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=['今日已签到'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/attendance.php',
                method=self.sign_in_by_douban,
                succeed_regex=['这是您的首次签到，本次签到获得.*?个魔力值。',
                               '签到成功，这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?个魔力值。',
                               '重新签到成功，本次签到获得.*?个魔力值'],
                assert_state=(check_final_state, SignState.SUCCEED)
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'downloaded': None,
                'share_ratio': None,
                'seeding': {
                    'regex': '活动种子.*?(\\d+)'
                },
                'leeching': {
                    'regex': '活动种子.*?\\d+\\D+(\\d+)'
                },
                'hr': {
                    'regex': 'H&R.*?(\\d+)',
                    'handle': self.handle_hr
                }

            }
        })
        return selector

    def sign_in_by_douban(self, entry: SignInEntry, config: dict, work: Work, last_content: str):
        if break_match := re.search(self.BREAK_REGEX, last_content):
            if int(break_match.group(1)) > 0:
                params = self.CONFIRM
            else:
                params = self.CANCEL
            response = self.request(entry, 'get', work.url, params=params)
            network_state = check_network_state(entry, response.url, response)
            if not network_state == NetworkState.SUCCEED:
                return
            last_content = net_utils.decode(response)
        if img_match := re.search(self.IMG_REGEX, last_content):
            img_name = img_match.group(1)
            answers = re.findall(self.ANSWER_REGEX, last_content)
            answer = self.get_answer(config, img_name, answers)
            if not answer:
                entry.fail_with_prefix('Cannot find answer')
                logger.info(f'img_name: {img_name}, answers: {answers}')
                return
            data = {
                'answer': answer,
                'submit': '提交'
            }
            return self.request(entry, 'post', work.url, data=data)
        entry.fail_with_prefix('Cannot find img_name')
        logger.info(f'last_content: {last_content}')
        return

    def get_answer(self, config, img_name, answers):
        for value, answer in answers:
            movies = requests.get(f'https://movie.douban.com/j/subject_suggest?q={answer}',
                                  headers={'user-agent': config.get('user-agent')}).json()
            for movie in movies:
                if img_name in movie.get('img'):
                    return value

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config, ignore_title=self.IGNORE_TITLE)

    def handle_hr(self, hr):
        return str(100 - int(hr))

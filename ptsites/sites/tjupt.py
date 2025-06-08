import json
import re
from io import BytesIO
from pathlib import Path
from time import sleep
from typing import Final
from urllib.parse import urljoin

import numpy as np
import requests
from PIL import Image
from flexget.utils.soup import get_soup
from loguru import logger

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://tjupt.org/'
    BREAK_REGEX: Final = r'已断签.*?天，当前可补签天数为 <b>(\d+)</b> 天'
    IMG_SELECTOR: Final = 'table.captcha img'
    ANSWER_SELECTOR: Final = 'table.captcha form > table > tbody > tr:nth-child(2) > td'
    CONFIRM: Final = {'action': 'confirm'}
    CANCEL: Final = {'action': 'cancel'}
    IGNORE_TITLE = '您正在下载或做种的种子被删除'
    USER_CLASSES: Final = {
        'uploaded': [5368709120000, 53687091200000],
        'days': [336, 924]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        entry['extra_msg'] = f'未签到: {urljoin(self.URL, "/attendance.php")}'
        return [
            Work(
                # url='/attendance.php',
                url='/',
                method=self.sign_in_by_get,
                # succeed_regex=['今日已签到'],
                succeed_regex=['欢迎'],
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
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > tbody > tr > td',
                    }
                }
            },
            'details': {
                'downloaded': None,
                'share_ratio': None,
                'seeding': {
                    'regex': '种子数合计.*?(\\d+)'
                },
                'leeching': {
                    'regex': '种子数合计.*?\\d+\\D+(\\d+)'
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
        captcha_el = get_soup(last_content).select_one(self.IMG_SELECTOR)
        answer_el = get_soup(last_content).select_one(self.ANSWER_SELECTOR)
        value = list(map(lambda x: x['value'], answer_el.select('input')))
        answer = get_soup(str(answer_el).replace('<br/>', '|')).text.split('|')[0:-1]

        answers = list(zip(value, answer))

        captcha_img_url = urljoin(self.URL, captcha_el['src'])

        answer = self.get_answer(entry, config, captcha_img_url, answers)
        if not answer:
            return
        data = {
            'answer': answer,
            'submit': '提交'
        }
        return self.request(entry, 'post', work.url, data=data)

    def get_answer(self, entry, config, captcha_img_url, answers):
        question_file = Path(__file__).parent.parent.joinpath(f'data/{entry["site_name"]}.json')
        if question_file.is_file():
            question_json = json.loads(question_file.read_text(encoding='utf-8'))
        else:
            question_json = {}
        img_name = captcha_img_url.split('/')[-1]
        cache_question = question_json.get(img_name)
        if cache_question:
            cache_answer = cache_question.get('answer')
            for value, answer in answers:
                if cache_answer == answer:
                    return value
            entry.fail_with_prefix('cache error!')
            return None

        captcha_img_response = self.request(entry, 'get', captcha_img_url)
        if captcha_img_response is None or captcha_img_response.status_code != 200:
            entry.fail_with_prefix('Can not get captcha_img')
            return None
        captcha_img = Image.open(BytesIO(captcha_img_response.content))
        captcha_img_hash = toHash(captcha_img)

        for value, answer in answers:
            logger.info((value, answer))
            skip = False
            for q in question_json.values():
                if q['answer'] == answer:
                    skip = True
            if skip:
                logger.info('skip')
                continue
            movies = requests.get(f'https://movie.douban.com/j/subject_suggest?q={answer}',
                                  headers={'user-agent': config.get('user-agent')}).json()
            if len(movies) == 0:
                logger.info(f'https://movie.douban.com/j/subject_suggest?q={answer} length: 0')
            for movie in movies:
                movie_img_response = requests.get(movie.get('img'))
                if movie_img_response is None or movie_img_response.status_code != 200:
                    entry.fail_with_prefix('douban error!')
                    return None
                movie_img = Image.open(BytesIO(movie_img_response.content))
                movie_img_hash = toHash(movie_img)
                score = compareHash(captcha_img_hash, movie_img_hash)
                logger.info(f'{movie.get("title")} url:{movie.get("img")} score: {score}')
                if score > 0.9:
                    question_json[img_name] = {
                        'hash': captcha_img_hash,
                        'answer': answer
                    }
                    question_file.write_text(json.dumps(question_json, indent=4, ensure_ascii=False), encoding='utf-8')
                    return value
                sleep(5)
        logger.info(f'img_name: {captcha_img_url}, answers: {answers}')
        logger.info(json.dumps({
            img_name: {
                'hash': captcha_img_hash,
                'answer': ''
            }
        }, indent=4, ensure_ascii=False))
        entry.fail_with_prefix('Cannot find answer')
        return None

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config, ignore_title=self.IGNORE_TITLE)

    def handle_hr(self, hr):
        return str(100 - int(hr))


def toHash(img, shape=(10, 10)):
    img = img.resize(shape)
    gray = np.asarray(img.convert('L'))
    s = 0
    hash_str = ''
    for i in range(shape[0]):
        for j in range(shape[1]):
            s = s + gray[i, j]
    avg = s / 100
    for i in range(shape[0]):
        for j in range(shape[1]):
            if gray[i, j] > avg:
                hash_str = hash_str + '1'
            else:
                hash_str = hash_str + '0'
    return hash_str


def compareHash(hash1, hash2, shape=(10, 10)):
    n = 0
    if len(hash1) != len(hash2):
        return -1
    for i in range(len(hash1)):
        if hash1[i] == hash2[i]:
            n = n + 1
    return n / (shape[0] * shape[1])

from __future__ import annotations

import itertools
import re
import time
from io import BytesIO
from pathlib import Path
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import NetworkState, check_network_state
from ..base.reseed import ReseedPasskey
from ..base.sign_in import SignState, check_sign_in_state, check_final_state
from ..base.work import Work
from ..utils import net_utils, baidu_ocr, dmhy_image
from ..utils.net_utils import get_module_name

try:
    from fuzzywuzzy import fuzz, process
except ImportError:
    fuzz = None
    process = None

from loguru import logger

from ..schema.nexusphp import NexusPHP

try:
    from PIL import Image
except ImportError:
    Image = None

_RETRY = 20
_CHAR_COUNT = 4
_SCORE = 40


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://u2.dmhy.org/'
    USERNAME_REGEX: Final = '<bdo dir=\'ltr\'>{username}</bdo>'
    SUCCEED_REGEX: Final = '.{0,500}奖励UCoin: <b>\\d+'
    USER_CLASSES: Final = {
        'downloaded': [3298534883328],
        'share_ratio': [4.55],
        'days': [700]
    }

    DATA = {
        'regex_keys': ['<input type="submit" name="(captcha_.*?)" value="(.*?)" />'],
        'req': '<input type="hidden" name="req" value="(.*?)" />',
        'hash': '<input type="hidden" name="hash" value="(.*?)" />',
        'form': '<input type="hidden" name="form" value="(.*?)" />'
    }

    def __init__(self):
        super().__init__()
        self.times = 0

    @classmethod
    def sign_in_build_schema(cls):
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'cookie': {'type': 'string'},
                    'comment': {'type': 'string'},
                    'ocr_config': {
                        'type': 'object',
                        'properties': {
                            'retry': {'type': 'integer'},
                            'char_count': {'type': 'integer'},
                            'score': {'type': 'integer'}
                        },
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        site_config = entry['site_config']
        succeed_regex = [self.USERNAME_REGEX.format(username=site_config.get('username')) + self.SUCCEED_REGEX,
                         '<a href="showup.php">已[签簽]到</a>']
        return [
            Work(
                url='/showup.php?action=show',
                method=self.sign_in_by_get,
                succeed_regex=succeed_regex,
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/showup.php?action=show',
                method=self.sign_in_by_anime,
                data=self.DATA,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                img_regex='image\\.php\\?action=adbc2&req=.+?(?=&imagehash)',
                reload_regex='image\\.php\\?action=reload_adbc2&div=showup&rand=\\d+'
            ),
            Work(
                url='/showup.php?action=show',
                method=self.sign_in_by_get,
                succeed_regex=succeed_regex,
                fail_regex='这是一个杯具。<br />验证码已过期。',
                assert_state=(check_final_state, SignState.SUCCEED)
            )
        ]

    def sign_in_by_anime(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not fuzz or not process:
            entry.fail_with_prefix('Dependency does not exist: [fuzzywuzzy]')
            return None

        ocr_config = entry['site_config'].get('ocr_config', {})
        ocr_config.setdefault('retry', _RETRY)
        ocr_config.setdefault('char_count', _CHAR_COUNT)
        ocr_config.setdefault('score', _SCORE)

        if not (data := self.build_data(entry, config, work, last_content, ocr_config)):
            entry.fail_with_prefix('Maximum number of retries reached' if self.times == ocr_config.get('retry')
                                   else 'Can not build_data')
            return None
        logger.info(data)
        return self.request(entry, 'post', work.url, data=data)

    def build_data(self, entry: SignInEntry, config: dict, work: Work, base_content: str,
                   ocr_config: dict) -> dict | None:
        if entry.failed:
            return None
        if not (img_url_match := re.search(work.img_regex, base_content)):
            entry.fail_with_prefix('Can not found img_url')
            return None
        img_url = img_url_match.group()
        logger.debug('attempts: {} / {}, url: {}', self.times, ocr_config.get('retry'), urljoin(entry['url'], img_url))
        data = {}
        found = False
        if images := self.get_image(entry, config, img_url, ocr_config.get('char_count')):
            image1, image2 = images
            self.save_iamge(image1, 'step3_a_diff.png')
            self.save_iamge(image2, 'step3_b_diff.png')
            ocr_text1 = baidu_ocr.get_jap_ocr(image1, entry, config)
            ocr_text2 = baidu_ocr.get_jap_ocr(image2, entry, config)
            if entry.failed:
                return None
            oct_text = ocr_text1 if len(ocr_text1) > len(ocr_text2) else ocr_text2
            logger.debug('jap_ocr: {}', oct_text)
            if oct_text and len(oct_text) > ocr_config['char_count']:
                for key, regex in work.data.items():
                    if key == 'regex_keys':
                        for regex_key in regex:
                            select = {}
                            ratio_score = 0
                            if not (regex_key_search := re.findall(regex_key, base_content, re.DOTALL)):
                                entry.fail_with_prefix(
                                    'Cannot find regex_key: {}, url: {}'.format(regex_key, work.url))
                                return None
                            for captcha, value in regex_key_search:
                                if answer_list := list(filter(lambda x2: len(x2) > 0,
                                                              map(lambda x: ''.join(re.findall(r'[\u2E80-\u9FFF]', x)
                                                                                    ), value.split('\n')))):
                                    split_value, partial_ratio = process.extractOne(oct_text, answer_list,
                                                                                    scorer=fuzz.partial_ratio)
                                else:
                                    partial_ratio = 0
                                if partial_ratio > ratio_score:
                                    select = (captcha, value)
                                    ratio_score = partial_ratio
                                logger.debug('value: {}, ratio: {}', value.replace('\n', '\\'), partial_ratio)
                            if ratio_score and ratio_score > ocr_config['score']:
                                captcha, value = select
                                data[captcha] = value
                                found = True
                    else:
                        if not (value_search := re.search(regex, base_content, re.DOTALL)):
                            entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, work.url))
                            return None
                        data[key] = value_search.group(1)

        if not found:
            if self.times >= ocr_config.get('retry'):
                return None
            self.times += 1
            reload_url = re.search(work.reload_regex, base_content).group()
            real_reload_url = urljoin(entry['url'], reload_url)
            reload_response = self.request(entry, 'get', real_reload_url)
            reload__net_state = check_network_state(entry, real_reload_url, reload_response)
            if reload__net_state != NetworkState.SUCCEED:
                return None
            reload_content = net_utils.decode(reload_response)
            return self.build_data(entry, config, work, reload_content, ocr_config)
        site_config = entry['site_config']
        data['message'] = site_config.get('comment')
        return data

    def get_image(self, entry: SignInEntry, config: dict, img_url: str, char_count: int) -> tuple | None:
        image_list = []
        checked_list = []
        images_sort_match = None
        new_image = self.get_new_image(entry, img_url)
        if not dmhy_image.check_analysis(new_image):
            self.save_iamge(new_image, 'z_failed.png')
            logger.debug('can not analyzed!')
            return None
        original_text = baidu_ocr.get_jap_ocr(new_image, entry, config)
        logger.debug('original_ocr: {}', original_text)
        if original_text is None or len(original_text) < char_count:
            return None
        image_list.append(new_image)
        while not images_sort_match and len(image_list) < 8:
            if not (new_image := self.get_new_image(entry, img_url)):
                return None
            image_list.append(new_image)
            for images in list(itertools.combinations(image_list, 2)):
                if images not in checked_list:
                    checked_list.append(images)
                    image1, image2 = images
                    self.save_iamge(image1, 'step1_a_original.png')
                    self.save_iamge(image2, 'step1_b_original.png')
                    if dmhy_image.compare_images_sort(image1, image2):
                        images_sort_match = images
                        break
        if images_sort_match:
            image1, image2 = images_sort_match
            image_a_split_1, image_a_split_2 = dmhy_image.split_image(image1)
            self.save_iamge(image_a_split_1, 'step2_a_split_1.png')
            self.save_iamge(image_a_split_2, 'step2_a_split_2.png')
            image_b_split_1, image_b_split_2 = dmhy_image.split_image(image2)
            self.save_iamge(image_b_split_1, 'step2_b_split_1.png')
            self.save_iamge(image_b_split_2, 'step2_b_split_2.png')
            image_last = dmhy_image.compare_images(image_a_split_1, image_b_split_1)
            image_last2 = dmhy_image.compare_images(image_a_split_2, image_b_split_2)
            if image_last and not image_last2:
                self.save_iamge(image_last[0], 'step3_a_split_1_diff.png')
                self.save_iamge(image_last[1], 'step3_b_split_1_diff.png')
                self.save_iamge(image_last[2], 'step4_split_1_diff.png')
                question_image = (image_last[0], image_last[1])
            elif image_last2 and not image_last:
                self.save_iamge(image_last2[0], 'step3_a_split_2_diff.png')
                self.save_iamge(image_last2[1], 'step3_b_split_2_diff.png')
                self.save_iamge(image_last2[2], 'step4_split_2_diff.png')
                question_image = (image_last2[0], image_last2[1])
            elif image_last:
                logger.debug('compare_images: Two identical are returned')
                self.save_iamge(image1, 'identical.png')
                self.save_iamge(image2, 'identical.png')
                self.save_iamge(image_last[0], 'identical_a_split_1_diff.png')
                self.save_iamge(image_last[1], 'identical_b_split_1_diff.png')
                self.save_iamge(image_last[2], 'identical_split_1_diff.png')
                self.save_iamge(image_last2[0], 'identical_a_split_2_diff.png')
                self.save_iamge(image_last2[1], 'identical_b_split_2_diff.png')
                self.save_iamge(image_last2[2], 'identical_split_2_diff.png')
                return None
            else:
                logger.debug('compare_images: no Content')
                return None
            return question_image
        return None

    def get_new_image(self, entry: SignInEntry, img_url: str) -> Image.Image | None:
        time.sleep(3)
        logger.debug('request image...')
        real_img_url = urljoin(entry['url'], img_url)
        base_img_response = self.request(entry, 'get', real_img_url)
        if base_img_response is None or base_img_response.status_code != 200 or base_img_response.url == urljoin(
                entry['url'], '/pic/trans.gif?debug=NIM'):
            return None
        new_image = Image.open(BytesIO(base_img_response.content))
        dmhy_image.remove_date_string(new_image)
        return new_image

    def save_iamge(self, new_image: Image.Image | None, path: str) -> None:
        if not Path('dmhy').is_dir():
            return
        if new_image:
            new_image.save('dmhy/' + path)

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'uploaded': {
                    'regex': r'上传量:  ([\d.]+ [ZEPTGMK]?i?B)'
                    # 'handle': self.handle_suffix
                },
                'downloaded': {
                    'regex': r'下载量:  ([\d.]+ [ZEPTGMK]?i?B)'
                    # 'handle': self.handle_suffix
                },
                'points': {
                    'regex': r'UCoin.*?\d+\(([\d,.]+)'
                },
                'seeding': {
                    'regex': r'客户端.*?: \d+ \((\d+)'
                },
                'leeching': {
                    'regex': r'客户端.*?: \d+ \(\d+ (\d+)'
                },
                'hr': None
            }
        })
        return selector

    # def handle_suffix(self, value: str):
    #     return value.replace('烫', 'TiB')
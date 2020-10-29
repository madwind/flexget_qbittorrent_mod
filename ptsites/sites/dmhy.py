import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

from fuzzywuzzy import fuzz, process
from loguru import logger

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState
from ..utils.baidu_ocr import BaiduOcr

try:
    from PIL import Image
except ImportError:
    Image = None

# auto_sign_in

BASE_URL = 'https://u2.dmhy.org/'
URL = 'https://u2.dmhy.org/showup.php?action=show'
USERNAME_REGEX = '<bdo dir=\'ltr\'>{username}</bdo>'
SUCCEED_REGEX = '.{0,500}奖励UCoin: <b>\\d+|<a href="showup.php">已签到</a>'
IMG_REGEX = 'image\\.php\\?action=adbc2&req=.+?(?=&imagehash)'
RELOAD_REGEX = 'image\\.php\\?action=reload_adbc2&div=showup&rand=\\d+'
DATA = {
    'regex_keys': ['<input type="submit" name="(captcha_.*?)" value="(.*?)" />'],
    'req': '<input type="hidden" name="req" value="(.*?)" />',
    'hash': '<input type="hidden" name="hash" value="(.*?)" />',
    'form': '<input type="hidden" name="form" value="(.*?)" />'
}


# site_config
#    username: 'xxxxx'
#    cookie: 'xxxxxxxx'
#    comment: 'xxxxxx'
#    ocr_config:
#      retry: 10
#      char_count: 2
#      score: 10


class MainClass(NexusPHP):
    def __init__(self):
        super(NexusPHP, self).__init__()
        self.times = 0

    @staticmethod
    def build_sign_in(entry, config):
        site_config = entry['site_config']
        entry['url'] = URL
        entry['succeed_regex'] = USERNAME_REGEX.format(username=site_config.get('username')) + SUCCEED_REGEX
        entry['base_url'] = BASE_URL
        headers = {
            'cookie': site_config.get('cookie'),
            'user-agent': config.get('user-agent'),
            'referer': BASE_URL
        }
        entry['headers'] = headers
        entry['data'] = DATA

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': ('UCoin.*?([\\d,.]+)\\(([\\d,.]+)\\)', 2)
                },
                'seeding': {
                    'regex': ('客户端.*?(\\d+).*?(\\d+).*?(\\d+)', 2)
                },
                'leeching': {
                    'regex': ('客户端.*?(\\d+).*?(\\d+).*?(\\d+)', 3)
                },
                'hr': None
            }
        })
        return selector

    def build_data(self, entry, base_content, config, retry, char_count, score):
        img_url = re.search(IMG_REGEX, base_content).group()
        img_response = self._request(entry, 'get', urljoin(BASE_URL, img_url))
        img_net_state = self.check_net_state(entry, img_response, urljoin(BASE_URL, urljoin(BASE_URL, img_url)))
        if img_net_state:
            return None
        code_file = Path('dmhy.png')
        code_file.write_bytes(img_response.content)
        img = Image.open(BytesIO(img_response.content))
        web_image_text = BaiduOcr.get_jap_ocr(img, entry, config)
        logger.info('web_image: {}', web_image_text)
        webimage_text = BaiduOcr.get_jap_ocr(img, entry, config)
        logger.info('jap_ocr: {}', webimage_text)
        data = {}
        found = False
        if webimage_text and len(webimage_text) > char_count:
            for key, regex in entry.get('data', {}).items():
                if key == 'regex_keys':
                    for regex_key in regex:
                        regex_key_search = re.findall(regex_key, base_content, re.DOTALL)
                        select = {}
                        ratio_score = 0
                        if regex_key_search:
                            for captcha, value in regex_key_search:
                                split_value, partial_ratio = process.extractOne(webimage_text, value.split('\n'),
                                                                                scorer=fuzz.partial_ratio)
                                if partial_ratio > ratio_score:
                                    select = (captcha, value)
                                    ratio_score = partial_ratio
                                logger.info('value: {}, ratio: {}', value.replace('\n', '\\'), partial_ratio)
                        else:
                            entry.fail_with_prefix('Cannot find regex_key: {}, url: {}'.format(regex_key, entry['url']))
                            return None
                        if ratio_score and ratio_score > score:
                            captcha, value = select
                            data[captcha] = value
                            found = True
                else:
                    value_search = re.search(regex, base_content, re.DOTALL)
                    if value_search:
                        data[key] = value_search.group(1)
                    else:
                        entry.fail_with_prefix('Cannot find key: {}, url: {}'.format(key, entry['url']))
                        return

        if not found and self.times < retry:
            self.times += 1
            reload_url = re.search(RELOAD_REGEX, base_content).group()
            reload_response = self._request(entry, 'get', urljoin(BASE_URL, reload_url))
            reload__net_state = self.check_net_state(entry, reload_response, urljoin(BASE_URL, reload_url))
            if reload__net_state:
                return None
            reload_content = self._decode(reload_response)
            return self.build_data(entry, reload_content, config, retry, char_count, score)
        site_config = entry['site_config']
        data['message'] = site_config.get('comment')
        return data

    def sign_in(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', entry['url'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, entry['url'])
        if sign_in_state != SignState.NO_SIGN_IN:
            return
        ocr_config = entry['site_config'].get('ocr_config')
        retry = 10
        char_count = 2
        score = 10
        if ocr_config:
            retry = ocr_config.get('retry', 10)
            char_count = ocr_config.get('char_count', 2)
            score = ocr_config.get('score', 10)
        data = self.build_data(entry, base_content, config, retry, char_count, score)
        if not data:
            entry.fail_with_prefix('Cannot build_data')
            return
        logger.info(data)
        post_answer_response = self._request(entry, 'post', entry['url'], data=data)
        post_answer_net_state = self.check_net_state(entry, post_answer_response, entry['url'])
        if post_answer_net_state:
            return
        response = self._request(entry, 'get', entry['url'])
        self.final_check(entry, response, entry['url'])

    def check_sign_in_state(self, entry, response, original_url, regex=None):
        net_state = self.check_net_state(entry, response, original_url)
        if net_state:
            return net_state, None

        content = self._decode(response)
        succeed_regex = regex if regex else entry.get('succeed_regex')

        succeed_list = re.findall(succeed_regex, content, re.DOTALL)
        if succeed_list:
            entry['result'] = re.sub('<.*?>|&shy;', '', succeed_list[-1])
            return SignState.SUCCEED, content
        return SignState.NO_SIGN_IN, content

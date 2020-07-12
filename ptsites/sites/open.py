import os
import re
from io import BytesIO
from urllib.parse import urljoin

from ..executor import Executor, SignState
from ..utils.baidu_ocr import BaiduOcr

try:
    from PIL import Image
except ImportError:
    Image = None

# auto_sign_in
BASE_URL = 'https://open.cd/'
URL = 'https://open.cd/plugin_sign-in.php'
SUCCEED_REGEX = '查看簽到記錄|{"state":"success","signindays":"\\d+","integral":"\\d+"}'
WRONG_REGEX = '验证码错误'

# html_rss
ROOT_ELEMENT_SELECTOR = '#form_torrent > table > tbody > tr:not(:first-child)'
FIELDS = {
    'title': {
        'element_selector': 'a[href*="details.php"]',
        'attribute': 'title'
    },
    'url': {
        'element_selector': 'a[href*="download.php"]',
        'attribute': 'href'
    },
    'promotion': {
        'element_selector': 'div[style="padding-bottom: 5px"] > img',
        'attribute': 'alt'
    },
    'progress': {
        'element_selector': '.progress_completed',
        'attribute': 'class'
    }
}


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX, base_url=BASE_URL,
                                            wrong_regex=WRONG_REGEX)

    @staticmethod
    def build_html_rss_config(config):
        config['root_element_selector'] = ROOT_ELEMENT_SELECTOR
        config['fields'] = FIELDS

    def do_sign_in(self, entry, config):
        base_response = self._request(entry, 'get', BASE_URL, headers=entry['headers'])
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, BASE_URL)
        if sign_in_state != SignState.NO_SIGN_IN:
            return

        image_hash_response = self._request(entry, 'get', URL)
        image_hash_state = self.check_net_state(entry, image_hash_response, URL)
        if image_hash_state:
            return
        image_hash_content = self._decode(image_hash_response)
        image_hash_re = re.search('(?<=imagehash=).*?(?=")', image_hash_content)
        img_src_re = re.search('(?<=img src=").*?(?=")', image_hash_content)

        if image_hash_re and img_src_re:
            image_hash = image_hash_re.group()
            img_src = img_src_re.group()
            img_url = urljoin(URL, img_src)
            img_response = self._request(entry, 'get', img_url)
            img_net_state = self.check_net_state(entry, img_response, img_url)
            if img_net_state:
                return
        else:
            entry['result'] = 'Cannot find key: image_hash'
            entry.fail(entry['result'])
            return

        img = Image.open(BytesIO(img_response.content))
        code, img_byte_arr = BaiduOcr.get_ocr_code(img, entry, config)
        if len(code) == 6:
            params = {
                'cmd': 'signin'
            }
            data = {
                'imagehash': (None, image_hash),
                'imagestring': (None, code)
            }
            response = self._request(entry, 'post', URL, files=data, params=params)
            final_state = self.final_check(entry, response, response.request.url)
        if len(code) != 6 or final_state == SignState.WRONG_ANSWER:
            with open(os.path.dirname(__file__) + "/opencd.png", "wb") as code_file:
                code_file.write(img_response.content)
            with open(os.path.dirname(__file__) + "/opencd.png", "wb") as code_file:
                code_file.write(img_byte_arr.getvalue())
            entry['result'] = 'ocr failed: {}, see opencd.png'.format(code)
            entry.fail(entry['result'])

import json
import os
from io import BytesIO

from ..schema.site_base import SiteBase
from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState
from ..utils.baidu_ocr import BaiduOcr

try:
    from PIL import Image
except ImportError:
    Image = None

# auto_sign_in
BASE_URL = 'https://hdsky.me/'
IMAGE_HASH_URL = 'https://hdsky.me/image_code_ajax.php'
IMAGE_URL = 'https://hdsky.me/image.php?action=regimage&imagehash={}'
URL = 'https://hdsky.me/showup.php'
SUCCEED_REGEX = '已签到|{"success":true,"message":\\d+}'
WRONG_REGEX = '{"success":false,"message":"invalid_imagehash"}'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX, base_url=BASE_URL,
                                     wrong_regex=WRONG_REGEX)

    def sign_in(self, entry, config):
        entry['base_response'] = base_response = self._request(entry, 'get', BASE_URL)
        sign_in_state, base_content = self.check_sign_in_state(entry, base_response, BASE_URL)
        if sign_in_state != SignState.NO_SIGN_IN:
            return

        data = {
            'action': (None, 'new')
        }

        image_hash_response = self._request(entry, 'post', IMAGE_HASH_URL, files=data)
        image_hash_net_state = self.check_net_state(entry, image_hash_response, IMAGE_HASH_URL)
        if image_hash_net_state:
            return
        content = self._decode(image_hash_response)
        image_hash = json.loads(content)['code']

        if image_hash:
            img_url = IMAGE_URL.format(image_hash)
            img_response = self._request(entry, 'get', img_url)
            img_net_state = self.check_net_state(entry, img_response, img_url)
            if img_net_state:
                return
        else:
            entry['result'] = 'Cannot find: image_hash'
            entry.fail(entry['result'])
            return
        img = Image.open(BytesIO(img_response.content))
        code, img_byte_arr = BaiduOcr.get_ocr_code(img, entry, config)
        if not entry.failed:
            if len(code) == 6:
                data = {
                    'action': (None, 'showup'),
                    'imagehash': (None, image_hash),
                    'imagestring': (None, code)
                }
                response = self._request(entry, 'post', URL, files=data)
                final_state = self.final_check(entry, response, response.request.url)
            if len(code) != 6 or final_state == SignState.WRONG_ANSWER:
                with open(os.path.dirname(__file__) + "/hdsky.png", "wb") as code_file:
                    code_file.write(img_response.content)
                with open(os.path.dirname(__file__) + "/hdsky2.png", "wb") as code_file:
                    code_file.write(img_byte_arr.getvalue())
                entry['result'] = 'ocr failed: {}, see hdsky.png'.format(code)
                entry.fail(entry['result'])

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        selector['details']['hr'] = None
        return selector

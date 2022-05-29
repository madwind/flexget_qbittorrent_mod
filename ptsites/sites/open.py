from __future__ import annotations

import re
from io import BytesIO
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import baidu_ocr
from ..utils import net_utils

try:
    from PIL import Image
except ImportError:
    Image = None


class MainClass(NexusPHP):
    URL: Final = 'https://open.cd/'
    USER_CLASSES: Final = {
        'downloaded': [644245094400, 3298534883328],
        'share_ratio': [3.5, 5],
        'days': [175, 210]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['查看簽到記錄'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/plugin_sign-in.php',
                method=self.sign_in_by_ocr,
                succeed_regex=['{"state":"success","signindays":"\\d+","integral":"\\d+"}'],
                fail_regex='验证码错误',
                response_urls=['/plugin_sign-in.php', '/plugin_sign-in.php?cmd=signin'],
                assert_state=(check_final_state, SignState.SUCCEED),
            ),
        ]

    def sign_in_by_ocr(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        image_hash_response = self.request(entry, 'get', work.url)
        image_hash_network_state = check_network_state(entry, work, image_hash_response)
        if image_hash_network_state != NetworkState.SUCCEED:
            entry.fail_with_prefix('Get image hash failed.')
            return None
        image_hash_content = net_utils.decode(image_hash_response)
        image_hash_re = re.search('(?<=imagehash=).*?(?=")', image_hash_content)
        img_src_re = re.search('(?<=img src=").*?(?=")', image_hash_content)

        if image_hash_re and img_src_re:
            image_hash = image_hash_re.group()
            img_src = img_src_re.group()
            img_url = urljoin(entry['url'], img_src)
            img_response = self.request(entry, 'get', img_url)
            img_network_state = check_network_state(entry, img_url, img_response)
            if img_network_state != NetworkState.SUCCEED:
                entry.fail_with_prefix('Get image failed.')
                return None
        else:
            entry.fail_with_prefix('Cannot find key: image_hash')
            return None

        img = Image.open(BytesIO(img_response.content))
        code, img_byte_arr = baidu_ocr.get_ocr_code(img, entry, config)
        if not entry.failed:
            if len(code) == 6:
                params = {
                    'cmd': 'signin'
                }
                data = {
                    'imagehash': (None, image_hash),
                    'imagestring': (None, code)
                }
                return self.request(entry, 'post', work.url, files=data, params=params)

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(2)'
                    }
                }
            }
        })
        return selector

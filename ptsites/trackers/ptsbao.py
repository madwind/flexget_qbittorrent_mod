from __future__ import annotations

import html
import re
from io import BytesIO
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.request import NetworkState, check_network_state
from ..base.reseed import ReseedPasskey
from ..base.sign_in import SignState, check_final_state, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import baidu_ocr, net_utils

try:
    from PIL import Image
except ImportError:
    Image = None


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://ptsbao.club/'
    SUCCEED_REGEX: Final = [
        '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?魔力值。|'
        '這是您的第.*次簽到，已連續簽到.*?天，本次簽到獲得.*?魔力值。',
        '[签簽]到已得\\d+',
        '您今天已经签到过了，请勿重复刷新。|您今天已經簽到過了，請勿重複刷新。',
    ]
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [112, 364],
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=self.SUCCEED_REGEX,
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/attendance.php',
                method=self.sign_in_by_ocr,
                succeed_regex=self.SUCCEED_REGEX,
                fail_regex='验证码错误|驗證碼錯誤',
                assert_state=(check_final_state, SignState.SUCCEED),
            ),
        ]

    def sign_in_by_ocr(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not Image:
            entry.fail_with_prefix('Dependency does not exist: [pillow]')
            return None
        if not (image_hash_match := re.search(
                r'name=["\']imagehash["\'][^>]*value=["\'](.*?)["\']', last_content)):
            entry.fail_with_prefix('Cannot find key: imagehash')
            return None
        if not (image_src_match := re.search(
                r'src=["\']([^"\']*image\.php\?action=regimage[^"\']*)["\']', last_content)):
            entry.fail_with_prefix('Cannot find captcha image URL')
            return None

        image_hash = image_hash_match.group(1)
        img_url = urljoin(entry['url'], html.unescape(image_src_match.group(1)))
        img_response = self.request(entry, 'get', img_url)
        if check_network_state(entry, img_url, img_response) != NetworkState.SUCCEED:
            entry.fail_with_prefix('Get image failed.')
            return None

        try:
            with Image.open(BytesIO(img_response.content)) as image:
                img = image.convert('RGB')
        except OSError:
            entry.fail_with_prefix('Invalid captcha image.')
            return None
        code, _ = baidu_ocr.get_ocr_code(img, entry, config)
        if entry.failed:
            return None
        if not code or not re.fullmatch(r'[A-Za-z0-9]{6}', code):
            entry.fail_with_prefix('Captcha OCR did not return six alphanumeric characters.')
            return None
        return self.request(entry, 'post', work.url, data={
            'imagehash': image_hash,
            'imagestring': code,
        })

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'uploaded': {
                    'regex': r'上传量:  ([\d,.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': r'下载量:  ([\d,.]+ [ZEPTGMK]?B)'
                },
                'points': {
                    'regex': r'魔力值.*?使用.*?([\d,.]+)'
                },
                'hr': None,
            }
        })
        return selector

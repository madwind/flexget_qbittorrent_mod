from __future__ import annotations

import re
from io import BytesIO
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, check_sign_in_state, SignState, Work
from ..schema.nexusphp import NexusPHP
from ..utils import baidu_ocr, net_utils

try:
    from PIL import Image
except ImportError:
    Image = None


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://www.oshen.win/'

    # 验证码隐藏字段，实测 oshen.win 的表单里就是这两个字段名
    IMAGEHASH_REGEX: Final = r'name=["\']imagehash["\']\s+value=["\']([^"\']+)["\']'
    # 验证码图片地址由 imagehash 直接拼出来，对应 NexusPHP image.php 里 action=regimage 的取图逻辑
    IMAGE_URL_TEMPLATE: Final = '/image.php?action=regimage&imagehash={}'

    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                # TODO: 把「今天已经签到过了」这类文案换成 oshen 实际显示的文字
                succeed_regex=[
                    '您今天已经签到过了|您今天已經簽到過了',
                    '[签簽]到已得\\d+',
                ],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/attendance.php',
                method=self.sign_in_by_ocr,
                # TODO: 把签到成功后的实际提示文案换进来，可以先跑一次看日志里 last_content 是什么
                succeed_regex=[
                    '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?[个個].*?[分币幣]。',
                    '簽到成功|签到成功',
                ],
                fail_regex='验证码错误|驗證碼錯誤|请输入正确的验证码',
                assert_state=(check_final_state, SignState.SUCCEED),
            ),
        ]

    def sign_in_by_ocr(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (imagehash_match := re.search(self.IMAGEHASH_REGEX, last_content)):
            entry.fail_with_prefix('Cannot find imagehash, page structure may have changed')
            return None
        if not Image:
            entry.fail_with_prefix('Dependency does not exist: [pillow]')
            return None

        imagehash = imagehash_match.group(1)
        img_url = urljoin(entry['url'], self.IMAGE_URL_TEMPLATE.format(imagehash))

        img_response = self.request(entry, 'get', img_url)
        if img_response is None or img_response.status_code != 200:
            entry.fail_with_prefix('Cannot get captcha image')
            return None

        img = Image.open(BytesIO(img_response.content))
        code, _ = baidu_ocr.get_ocr_code(img, entry, config)
        if entry.failed:
            return None
        # 截图里验证码是 6 位数字，长度不对就不用浪费一次提交了
        if not code or len(code) != 6:
            entry.fail_with_prefix(f'OCR result looks wrong: {code!r}')
            return None

        data = {
            'imagehash': imagehash,
            'imagestring': code,
        }
        return self.request(entry, 'post', work.url, data=data)

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                # oshen 页面上没有 H&R 这项统计，跳过它，不然默认的 H&R 正则会匹配不到而报错
                'hr': None
            }
        })
        return selector

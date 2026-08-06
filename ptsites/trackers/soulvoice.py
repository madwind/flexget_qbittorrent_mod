from __future__ import annotations

import re
from io import BytesIO
from time import sleep
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, check_sign_in_state, SignState, Work
from ..schema.nexusphp import AttendanceHR
from ..utils import baidu_ocr

try:
    from PIL import Image
except ImportError:
    Image = None


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://pt.soulvoice.club/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    # 站点新加了验证码，签到表单里的隐藏字段
    IMAGEHASH_REGEX: Final = r'name=["\']imagehash["\']\s+value=["\']([^"\']+)["\']'
    # 这里直接从页面里抠 <img> 的 src，而不是用 imagehash 自己拼 URL，
    # 因为这个站的图片地址除了 imagehash 还多带了一个 secret 参数
    IMG_SRC_REGEX: Final = r'<img[^>]+src=["\'](image\.php\?[^"\']*action=regimage[^"\']*)["\']'

    def request(self,
                entry: SignInEntry,
                method: str,
                url: str,
                **kwargs,
                ) -> Response | None:
        sleep(2)
        return super().request(entry, method, url, **kwargs)

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                # 顶部信息栏没签到时显示 “[签到得魔力]”，签过了才会变成 “签到已得X”
                succeed_regex=[
                    '您今天已经签到过了，请勿重复刷新。|您今天已經簽到過了，請勿重複刷新。',
                    '[签簽]到已得\\d+',
                ],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/attendance.php',
                method=self.sign_in_by_ocr,
                succeed_regex=[
                    '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?魔力值。'
                    '|這是您的第.*?次簽到，已連續簽到.*?天，本次簽到獲得.*?魔力值。',
                    '[签簽]到已得\\d+',
                ],
                fail_regex='验证码错误|驗證碼錯誤|请输入正确的验证码',
                assert_state=(check_final_state, SignState.SUCCEED),
            ),
        ]

    def sign_in_by_ocr(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        if not (imagehash_match := re.search(self.IMAGEHASH_REGEX, last_content)):
            entry.fail_with_prefix('Cannot find imagehash, page structure may have changed')
            return None
        if not (img_src_match := re.search(self.IMG_SRC_REGEX, last_content)):
            entry.fail_with_prefix('Cannot find captcha image src')
            return None
        if not Image:
            entry.fail_with_prefix('Dependency does not exist: [pillow]')
            return None

        imagehash = imagehash_match.group(1)
        # 页面里的 & 是 HTML 转义过的 &amp;，直接拿去请求会带错参数
        img_src = img_src_match.group(1).replace('&amp;', '&')
        img_url = urljoin(entry['url'], img_src)

        img_response = self.request(entry, 'get', img_url)
        if img_response is None or img_response.status_code != 200:
            entry.fail_with_prefix('Cannot get captcha image')
            return None

        img = Image.open(BytesIO(img_response.content))
        code, _ = baidu_ocr.get_ocr_code(img, entry, config)
        if entry.failed:
            return None
        # 验证码是 6 位字母数字，长度不对就别浪费一次提交了
        if not code or len(code) != 6:
            entry.fail_with_prefix(f'OCR result looks wrong: {code!r}')
            return None

        data = {
            'imagehash': imagehash,
            'imagestring': code,
        }
        return self.request(entry, 'post', work.url, data=data)

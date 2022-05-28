from __future__ import annotations

import re
from typing import Final
from urllib.parse import urljoin

from requests import Response

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.nexusphp import Attendance


class MainClass(Attendance):
    URL: Final = 'https://1ptba.com/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_param,
                succeed_regex=[
                    '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?魔力值。|這是您的第.*次簽到，已連續簽到.*?天，本次簽到獲得.*?魔力值。',
                    '[签簽]到已得\\d+',
                    '您今天已经签到过了，请勿重复刷新。|您今天已經簽到過了，請勿重複刷新。'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def sign_in_by_param(self, entry: SignInEntry, config: dict, work: Work,
                         last_content: str = None) -> Response | None:
        if response := self.request(entry, 'get', work.url):
            if location_match := re.search('window\\.location="(.*?);</script>', response.text):
                uri: str = re.sub('["+ ]', '', location_match.group(1))
                work.url = urljoin(work.url, uri)
                return self.sign_in_by_get(entry, config, work, last_content)
            return response
        return None

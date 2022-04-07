import re
from urllib.parse import urljoin

from ..schema.nexusphp import Attendance
from ..schema.site_base import Work, SignState


class MainClass(Attendance):
    URL = 'https://1ptba.com/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/attendance.php',
                method='param',
                succeed_regex=[
                    '这是您的第.*?次签到，已连续签到.*?天，本次签到获得.*?魔力值。|這是您的第.*次簽到，已連續簽到.*?天，本次簽到獲得.*?魔力值。',
                    '[签簽]到已得\\d+',
                    '您今天已经签到过了，请勿重复刷新。|您今天已經簽到過了，請勿重複刷新。'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def sign_in_by_param(self, entry, config, work, last_content=None):
        response = self._request(entry, 'get', work.url)
        if response:
            location_match = re.search('window\\.location="(.*?);</script>', response.text)
            if location_match:
                uri = re.sub('["|+| ]', '', location_match.group(1))
                work.url = urljoin(work.url, uri)
                return self.sign_in_by_get(entry, config, work, last_content)
            else:
                return response

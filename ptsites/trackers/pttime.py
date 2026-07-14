import re
from typing import Final

from requests import Response

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState, Work, check_sign_in_state
from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://www.pttime.org/'
    USER_CLASSES: Final = {
        'downloaded': [3221225472000, 16106127360000],
        'share_ratio': [3.05, 4.55],
        'days': [112, 364]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['签到详情'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/attendance.php?type=sign',
                method=self.sign_in_by_userid,
                succeed_regex=[
                    '签到成功',
                    '今天已签到，请勿重复刷新'],
                assert_state=(check_final_state, SignState.SUCCEED),
            )
        ]

    def sign_in_by_userid(self,
                          entry: SignInEntry,
                          config: dict,
                          work: Work,
                          last_content: str = None,
                          ) -> Response | None:
        if useridMatch := re.search(r'userdetails\.php\?id=(\d+)', last_content):
            userid = useridMatch.group(1)
            work.url = work.url + f'&uid={userid}'
            work.response_urls = [work.url]
            return super().sign_in_by_get(entry, config, work, last_content)

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block',
                    }
                },
            },
            'details': {
                'seeding': {
                    'regex': r'活动:.*?(\d+)'
                },
                'leeching': {
                    'regex': (r'活动:.*?(\d+).*?(\d+)', 2)
                },
            }
        })
        return selector

    def get_nexusphp_messages(self, entry: SignInEntry, config: dict, **kwargs) -> None:
        super().get_nexusphp_messages(entry, config, unread_elements_selector='td > i[alt*="Unread"]')

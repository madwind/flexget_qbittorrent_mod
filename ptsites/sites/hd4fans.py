from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState, NetworkState, Work
from ..utils.net_utils import NetUtils


class MainClass(NexusPHP):
    URL = 'https://pt.hd4fans.org/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    DATA = {
        'fixed': {
            'action': 'checkin'
        }
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<span id="checkedin">\\[签到成功\\]</span>',
                fail_regex=None,
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/checkin.php',
                method='post',
                data=self.DATA,
                succeed_regex=None,
                fail_regex=None,
                check_state=('network', NetworkState.SUCCEED)
            ),
            Work(
                url='/',
                method='get',
                succeed_regex='<span id="checkedin">\\[签到成功\\]</span>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED)
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

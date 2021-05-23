from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState, Work
from ..utils.net_utils import NetUtils


class MainClass(NexusPHP):
    URL = 'https://pt.hdupt.com/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [5.59, 8.85],
        'days': [280, 700]
    }
    DATA = {
        'fixed': {
            'action': (None, 'qiandao')
        }
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<span id="yiqiandao">\\[已签到\\]</span>',
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/added.php',
                method='post',
                data=self.DATA,
                succeed_regex='\\d+',
                check_state=('final', SignState.SUCCEED),
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

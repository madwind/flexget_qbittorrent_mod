from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState, Work
from ..utils.net_utils import NetUtils


class MainClass(NexusPHP):
    URL = 'https://pt.btschool.club/'
    USER_CLASSES = {
        'downloaded': [1099511627776, 10995116277760],
        'share_ratio': [3.05, 4.55],
        'points': [600000, 1000000],
        'days': [280, 700]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/index.php?action=addbonus',
                method='get',
                succeed_regex='欢迎回来',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': '做种积分: ([\\d.,]+)',
                }
            }
        })
        return selector

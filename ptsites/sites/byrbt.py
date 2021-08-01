from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState, Work
from ..utils.net_utils import NetUtils


class MainClass(NexusPHP):
    URL = 'https://bt.byr.cn/'
    USER_CLASSES = {
        'uploaded': [4398046511104, 140737488355328],
        'share_ratio': [3.05, 4.55],
        'days': [168, 336]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/index.php',
                method='get',
                succeed_regex='欢迎',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
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

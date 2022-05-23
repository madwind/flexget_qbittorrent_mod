from ..schema.nexusphp import NexusPHP
from ..schema.site_base import Work, SignState
from ..utils import net_utils


class MainClass(NexusPHP):
    URL = 'https://pterclub.com/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [210, 315]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['签到已得\\d+'],
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/attendance-ajax.php',
                method='get',
                succeed_regex=[
                    '这是您的第 .* 次签到，已连续签到 .* 天。.*本次签到获得 .* 克猫粮。',
                    '签到已得\\d+',
                    '您今天已经签到过了，请勿重复刷新。'
                ],
                check_state=('final', SignState.SUCCEED),
            )
        ]

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': '猫粮.*?([\\d,.]+)'
                }
            }
        })
        return selector

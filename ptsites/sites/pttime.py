from ..base.base import SignState, Work
from ..schema.nexusphp import Attendance
from ..utils import net_utils


class MainClass(Attendance):
    URL = 'https://www.pttime.org/'
    USER_CLASSES = {
        'downloaded': [3221225472000, 16106127360000],
        'share_ratio': [3.05, 4.55],
        'days': [112, 364]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/attendance.php',
                method='get',
                succeed_regex=[
                    '这是你的第.*?次签到，已连续签到.*天，本次签到获得.*个魔力值。',
                    '获得魔力值：\\d+',
                    '你今天已经签到过了，请勿重复刷新。'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block',
                        'table': '#outer table.main:last-child'
                    }
                }
            }
        })
        return selector

    def get_nexusphp_message(self, entry, config, **kwargs):
        super().get_nexusphp_message(entry, config, unread_elements_selector='td > i[alt*="Unread"]')

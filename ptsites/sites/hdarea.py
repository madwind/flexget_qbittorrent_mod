from ..schema.nexusphp import NexusPHP
from ..schema.site_base import Work, SignState


class MainClass(NexusPHP):
    URL = 'https://www.hdarea.co/'
    USER_CLASSES = {
        'downloaded': [1099511627776, 10995116277760],
        'share_ratio': [4.5, 6],
        'days': [140, 280]
    }

    DATA = {
        'fixed': {
            'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
            'signed_token': '(?<=signed_token: ").*(?=")'
        }
    }

    @classmethod
    def build_workflow(cls):
        return [
            Work(
                url='/torrents.php',
                method='get',
                succeed_regex='<span id="checkedin">\\[签到成功\\]</span>',
                fail_regex=None,
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/sign_in.php?action=sign_in',
                method='post',
                data=cls.DATA,
                succeed_regex='已连续签到.*天，此次签到您获得了.*魔力值奖励!|请不要重复签到哦！',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED)
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState, Work
from ..utils import net_utils


class MainClass(NexusPHP):
    URL = 'https://totheglory.im/'
    USER_CLASSES = {
        'uploaded': [769658139444, 109951162777600],
        'downloaded': [3848290697216, 10995116277760],
        'share_ratio': [5, 6],
        'days': [224, 336]
    }

    DATA = {
        'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
        'signed_token': '(?<=signed_token: ").*(?=")'
    }

    def sign_in(self, entry, config):
        entry.fail_with_prefix("公告禁止使用脚本，请移除")
        return

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['<b style="color:green;">已签到</b>'],
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/signed.php',
                method='post',
                data=self.DATA,
                succeed_regex=['您已连续签到\\d+天，奖励\\d+积分，明天继续签到将获得\\d+积分奖励。'],
                check_state=('final', SignState.SUCCEED),
            )
        ]

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'body > table:nth-child(3) > tbody > tr > td > table > tbody > tr > td:nth-child(1)',
                        'table': '#main_table > tbody > tr:nth-child(1) > td > table > tbody > tr > td > table > tbody'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': ('(上[传傳]量|Uploaded).+?([\\d.]+ ?[ZEPTGMk]?i?B)', 2),
                    'handle': self.handle_size
                },
                'downloaded': {
                    'regex': ('(下[载載]量|Downloaded).+?([\\d.]+ ?[ZEPTGMk]?i?B)', 2),
                    'handle': self.handle_size
                },
                'points': {
                    'regex': '积分.*?([\\d,.]+)'
                },
                'seeding': {
                    'regex': '做种活动.*?(\\d+)'
                },
                'leeching': {
                    'regex': '做种活动.*?\\d+\\D+(\\d+)'
                },
                'hr': {
                    'regex': 'HP.*?(\\d+)',
                    'handle': self.handle_hr
                }
            }
        })
        return selector

    def handle_size(self, size):
        return size.upper()

    def handle_hr(self, hr):
        return str(15 - int(hr))

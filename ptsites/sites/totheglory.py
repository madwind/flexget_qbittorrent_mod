from ..nexusphp import NexusPHP

# auto_sign_in
BASE_URL = 'https://totheglory.im/'
URL = 'https://totheglory.im/signed.php'
SUCCEED_REGEX = '<b style="color:green;">已签到</b>|您已连续签到\\d+天，奖励\\d+积分，明天继续签到将获得\\d+积分奖励。'
DATA = {
    'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
    'signed_token': '(?<=signed_token: ").*(?=")'
}


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        NexusPHP.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX, base_url=BASE_URL)
        entry['data'] = DATA

    def sign_in(self, entry, config):
        self.sign_in_by_post_data(entry, config)

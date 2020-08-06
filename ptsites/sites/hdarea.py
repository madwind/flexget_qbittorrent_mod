from ..nexusphp import NexusPHP

# auto_sign_in
BASE_URL = 'https://www.hdarea.co/torrents.php'
URL = 'https://www.hdarea.co/sign_in.php?action=sign_in'
SUCCEED_REGEX = '已连续签到.*天，此次签到您获得了.*魔力值奖励!|请不要重复签到哦！'
DATA = {
    'fixed': {
        'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
        'signed_token': '(?<=signed_token: ").*(?=")'
    }
}


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        NexusPHP.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX, base_url=BASE_URL)
        entry['data'] = DATA

    def sign_in(self, entry, config):
        self.sign_in_by_post_data(entry, config)

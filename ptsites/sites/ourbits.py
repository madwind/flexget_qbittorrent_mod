from ..schema.nexusphp import NexusPHP

# auto_sign_in
LOGIN_URL = 'https://ourbits.club/takelogin.php'
LOGIN_SUCCEED_URL = 'https://ourbits.club/index.php'
URL = 'https://ourbits.club/attendance.php'
SUCCEED_REGEX = '这是您的第 .* 次签到，已连续签到 .* 天，本次签到获得 .* 个魔力值。|您今天已经签到过了，请勿重复刷新。'


# site_config
# login:
#    username: 'xxxxx'
#    password: 'xxxxxxxx'

class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers

    def sign_in(self, entry, config):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return

        data = {
            '2fa_code': '',
            'trackerssl': 'yes',
            'username': login['username'],
            'password': login['password'],
        }

        login_response = self._request(entry, 'post', LOGIN_URL, data=data)
        login_state = self.check_net_state(entry, login_response, LOGIN_SUCCEED_URL)
        if login_state:
            entry.fail_with_prefix('Login failed!')
        else:
            self.sign_in_by_get(entry, config)

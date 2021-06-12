from ..schema.nexusphp import AttendanceHR

from ..schema.site_base import Work, NetworkState


# site_config
# login:
#    username: 'xxxxx'
#    password: 'xxxxxxxx'

class MainClass(AttendanceHR):
    URL = 'https://ourbits.club/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [175, 364]
    }

    def build_login_work(self, entry, config):
        return [
            Work(
                url='/takelogin.php',
                method='login',
                check_state=('network', NetworkState.SUCCEED),
                response_urls=['/index.php']
            )
        ]

    def sign_in_by_login(self, entry, config, work, last_content=None):
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
        return self._request(entry, 'post', work.url, data=data)

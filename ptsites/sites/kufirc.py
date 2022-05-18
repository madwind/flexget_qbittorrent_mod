import re

from ..schema.luminance import Luminance


class MainClass(Luminance):
    URL = 'https://kufirc.com/'
    USER_CLASSES = {
        'uploaded': [32985348833280],
        'share_ratio': [2.05],
        'days': [350]
    }

    def sign_in_by_password(self, entry, config, work, last_content):
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'cinfo': '1920|1080|24|-480',
            'iplocked': 0,
            'keeploggedin': [0, 1],
            'submit': 'Bejelentkezés',
        }
        return self._request(entry, 'post', work.url, data=data)

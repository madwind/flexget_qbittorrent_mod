import re

from ..schema.luminance import Luminance


class MainClass(Luminance):
    URL = 'https://www.happyfappy.org/'
    USER_CLASSES = {
        'uploaded': [54975581388800],
        'share_ratio': [7],
        'days': [196]
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
            'submit': 'Login',
        }
        return self._request(entry, 'post', work.url, data=data)

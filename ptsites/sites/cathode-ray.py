import re

from ..schema.luminance import Luminance


class MainClass(Luminance):
    URL = 'https://www.cathode-ray.tube/'
    USER_CLASSES = {
        'uploaded': [54975581388800],
        'share_ratio': [1],
        'days': [364]
    }

    def sign_in_by_password(self, entry, config, work, last_content):
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'cinfo': '1920|1080|1|24|-480',
            'iplocked': 0,
            'keeploggedin': [0, 1],
            'submit': 'login',
        }
        return self._request(entry, 'post', work.url, data=data)

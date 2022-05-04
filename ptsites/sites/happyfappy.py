import re

from ..schema.luminance import Luminance
from ..schema.site_base import NetworkState


class MainClass(Luminance):
    URL = 'https://www.happyfappy.org/'
    USER_CLASSES = {
        'uploaded': [54975581388800],
        'share_ratio': [7],
        'days': [196]
    }

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
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
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

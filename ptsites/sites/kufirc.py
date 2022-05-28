import re
from typing import Final

from ..schema.luminance import Luminance


class MainClass(Luminance):
    URL: Final = 'https://kufirc.com/'
    USER_CLASSES: Final = {
        'uploaded': [32985348833280],
        'share_ratio': [2.05],
        'days': [350]
    }

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'token': re.search(r'(?<=name="token" value=").*?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'cinfo': '1920|1080|24|-480',
            'iplocked': 0,
            'keeploggedin': [0, 1],
            'submit': 'Bejelentkezés',
        }

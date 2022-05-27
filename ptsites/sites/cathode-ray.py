import re
from typing import Final

from ..schema.luminance import Luminance


class MainClass(Luminance):
    URL: Final = 'https://www.cathode-ray.tube/'
    USER_CLASSES: Final = {
        'uploaded': [54975581388800],
        'share_ratio': [1],
        'days': [364]
    }

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'token': re.search(r'(?<=name="token" value=").*?(?=")', last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'cinfo': '1920|1080|1|24|-480',
            'iplocked': 0,
            'keeploggedin': [0, 1],
            'submit': 'login',
        }

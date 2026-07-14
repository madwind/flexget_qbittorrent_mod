from typing import Final

from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL: Final = 'https://pt.itzmx.com/'
    USER_CLASSES: Final = {
        'downloaded': [2147483648000, 1759218604442],
        'share_ratio': [4, 6],
        'days': [70, 1092]
    }

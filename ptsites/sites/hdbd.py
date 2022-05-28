from typing import Final

from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL: Final = 'https://pt.hdbd.us/'
    SUCCEED_REGEX: Final = '伊甸园 PT Torrents'
    USER_CLASSES: Final = {
        'downloaded': [3298534883328, 32985348833280],
        'share_ratio': [4, 16],
        'days': [336, 1274]
    }

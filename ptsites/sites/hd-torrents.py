from typing import Final

from ..schema.xbtit import XBTIT


class MainClass(XBTIT):
    URL: Final = 'https://hd-torrents.org/'
    SUCCEED_REGEX: Final = 'Welcome back, .+?!'
    USER_CLASSES: Final = {
        'uploaded': [1099511627776],
        'share_ratio': [4]
    }

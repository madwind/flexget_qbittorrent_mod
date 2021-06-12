from ..schema.xbtit import XBTIT


class MainClass(XBTIT):
    URL = 'https://hd-torrents.org/'
    SUCCEED_REGEX = 'Welcome back, .+?!'
    USER_CLASSES = {
        'uploaded': [1099511627776],
        'share_ratio': [4]
    }

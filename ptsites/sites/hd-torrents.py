from ..schema.xbtit import XBTIT


class MainClass(XBTIT):
    URL = 'https://hd-torrents.org/'
    SUCCEED_REGEX = 'Welcome back, .+?!'
    USER_CLASSES = {
        'uploaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [70]
    }

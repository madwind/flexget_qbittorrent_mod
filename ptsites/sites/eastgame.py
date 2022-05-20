from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL = 'https://pt.eastgame.org/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [5.05, 8.55],
        'days': [280, 385]
    }

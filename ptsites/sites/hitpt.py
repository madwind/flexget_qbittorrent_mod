from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL = 'https://www.hitpt.com/'
    USER_CLASSES = {
        'downloaded': [805306368000, 2199023255552],
        'share_ratio': [3.05, 4.05],
        'days': [56, 350]
    }

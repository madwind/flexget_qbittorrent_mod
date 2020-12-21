from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL = 'https://hdfans.org/'
    USER_CLASSES = {
        'downloaded': [4398046511104, 10995116277760],
        'share_ratio': [3.5, 5],
        'days': [210, 364]
    }

from ..schema.nexusphp import Bakatest


class MainClass(Bakatest):
    URL = 'https://yingk.com/'
    USER_CLASSES = {
        'uploaded': [17179869184, 140737488355328],
        'downloaded': [171798691840, 1099511627776],
        'share_ratio': [5, 8],
        'days': [175, 364]
    }

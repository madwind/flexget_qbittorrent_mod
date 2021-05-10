from ..schema.nexusphp import Attendance


class MainClass(Attendance):
    URL = 'https://ultrahd.net/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [5, 6.5],
        'days': [175, 280]
    }

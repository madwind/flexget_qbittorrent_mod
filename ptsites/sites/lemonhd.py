from ..schema.nexusphp import Attendance


class MainClass(Attendance):
    URL = 'https://lemonhd.org/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [175, 364]
    }

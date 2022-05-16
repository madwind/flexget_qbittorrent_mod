from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL = 'https://ptchina.org/'
    USER_CLASSES = {
        'downloaded': [805_306_368_000, 3_298_534_883_328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

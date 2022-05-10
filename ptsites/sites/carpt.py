from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL = 'https://carpt.net/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [6, 9],
        'days': [280, 700]
    }

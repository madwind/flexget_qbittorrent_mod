from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL = 'https://www.htpt.cc/'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

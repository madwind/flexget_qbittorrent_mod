from typing import Final

from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL: Final = 'https://carpt.net/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [6, 9],
        'days': [280, 700]
    }

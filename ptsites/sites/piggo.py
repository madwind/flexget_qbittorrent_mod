from typing import Final

from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL: Final = 'https://piggo.me/'
    USER_CLASSES: Final = {
        'downloaded': [2_199_023_255_552, 6_597_069_766_656],
        'share_ratio': [4, 6],
        'days': [280, 700]
    }

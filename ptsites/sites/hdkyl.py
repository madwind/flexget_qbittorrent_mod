from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import AttendanceHR
from ..utils.value_handler import size


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://www.hdkyl.in/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(10, 'TiB')],
        'share_ratio': [6, 10],
        'points': [400000, 1000000],
        'days': [280, 700]
    }

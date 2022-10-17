from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import AttendanceHR
from ..utils.value_handler import size


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://hhanclub.top/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(3, 'TiB')],
        'share_ratio': [3.05, 4.45],
        'days': [280, 700]
    }

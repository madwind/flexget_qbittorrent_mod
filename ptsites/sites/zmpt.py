from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils.value_handler import size


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://zmpt.cc/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(3, 'TiB')],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

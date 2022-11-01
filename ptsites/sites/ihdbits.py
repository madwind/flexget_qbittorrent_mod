from typing import Final

from ..schema.nexusphp import Attendance
from ..utils.value_handler import size


class MainClass(Attendance):
    URL: Final = 'https://ihdbits.me/'
    USER_CLASSES: Final = {
        'downloaded': [size(2048, 'GiB'), size(16384, 'TiB')],
        'share_ratio': [6, 10],
        'days': [280, 700]
    }

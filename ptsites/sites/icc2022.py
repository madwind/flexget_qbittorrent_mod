from __future__ import annotations

from typing import Final

from ..schema.nexusphp import Attendance
from ..utils.value_handler import size


class MainClass(Attendance):
    URL: Final = 'https://www.icc2022.com/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(3, 'TiB')],
        'share_ratio': [3.05, 4.45],
        'points': [400000, 1000000],
        'days': [280, 700]
    }

from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://hdfun.me/'
    USER_CLASSES: Final = {
        'downloaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [70]
    }

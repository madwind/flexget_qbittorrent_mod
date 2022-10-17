from typing import Final

from ..base.reseed import ReseedCookie
from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR, ReseedCookie):
    URL: Final = 'https://www.hddolby.com/'
    USER_CLASSES: Final = {
        'downloaded': [1099511627776, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [112, 336]
    }

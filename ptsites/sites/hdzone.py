from typing import Final

from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL: Final = 'https://hdzone.me/'
    USER_CLASSES: Final = {
        'downloaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [70]
    }

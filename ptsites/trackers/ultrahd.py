from typing import Final

from ..schema.nexusphp import Attendance


class MainClass(Attendance):
    URL: Final = 'https://ultrahd.net/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [5, 6.5],
        'days': [175, 280]
    }

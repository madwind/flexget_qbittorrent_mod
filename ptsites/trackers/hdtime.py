from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://hdtime.org/'
    USER_CLASSES: Final = {
        'downloaded': [1649267441664, 10995116277760],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

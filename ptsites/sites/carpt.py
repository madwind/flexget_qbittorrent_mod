from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://carpt.net/'
    IGNORE_TITLE = r'H&R\(ID: \d+\) 已达标'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [6, 9],
        'days': [280, 700]
    }

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config, ignore_title=self.IGNORE_TITLE)

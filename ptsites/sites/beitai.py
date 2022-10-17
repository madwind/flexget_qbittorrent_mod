from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://www.beitai.pt/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

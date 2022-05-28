from typing import Final

from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL: Final = 'https://www.beitai.pt/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

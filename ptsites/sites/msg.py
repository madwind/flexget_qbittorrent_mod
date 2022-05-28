from typing import Final

from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL: Final = 'https://pt.msg.vg/'
    USER_CLASSES: Final = {
        'downloaded': [1099511627776, 3298534883328],
        'share_ratio': [3.55, 4.55],
        'days': [420, 700]
    }

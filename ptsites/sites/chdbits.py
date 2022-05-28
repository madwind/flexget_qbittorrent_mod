from typing import Final

from ..schema.nexusphp import BakatestHR


class MainClass(BakatestHR):
    URL: Final = 'https://chdbits.co/'
    USER_CLASSES: Final = {
        'downloaded': [3298534883328, 4398046511104],
        'share_ratio': [8, 10],
        'points': [3500000, 5000000],
        'days': [280, 364]
    }

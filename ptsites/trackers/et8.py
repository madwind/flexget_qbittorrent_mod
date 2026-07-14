from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://et8.org/'
    USER_CLASSES: Final = {
        'downloaded': [1099511627776, 8796093022208],
        'share_ratio': [3.05, 4.55],
        'days': [266, 616]
    }

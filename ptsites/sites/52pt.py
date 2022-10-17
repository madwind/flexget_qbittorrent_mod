from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import BakatestHR


class MainClass(BakatestHR, ReseedPasskey):
    URL: Final = 'https://52pt.site/'
    USER_CLASSES: Final = {
        'downloaded': [2748779069440, 6047313952768],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

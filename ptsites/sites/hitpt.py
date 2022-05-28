from typing import Final

from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL: Final = 'https://www.hitpt.com/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 2199023255552],
        'share_ratio': [3.05, 4.05],
        'days': [56, 350]
    }

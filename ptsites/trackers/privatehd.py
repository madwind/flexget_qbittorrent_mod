from typing import Final

from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL: Final = 'https://privatehd.to/'
    SUCCEED_REGEX: Final = '<title>PrivateHD Beta 3.0</title>'

from typing import Final

from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL: Final = 'https://avistaz.to/'
    SUCCEED_REGEX: Final = '<title>AvistaZ Beta 3.0</title>'

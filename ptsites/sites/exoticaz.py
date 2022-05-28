from typing import Final

from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL: Final = 'https://exoticaz.to/'
    SUCCEED_REGEX: Final = 'Logout'

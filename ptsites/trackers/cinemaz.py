from typing import Final

from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL: Final = 'https://cinemaz.to/'
    SUCCEED_REGEX: Final = '<h1 class="title"><i class="fa fa-home"></i> CinemaZ Beta 3.0</h1>'

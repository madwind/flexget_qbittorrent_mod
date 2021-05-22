from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL = 'https://cinemaz.to/'
    SUCCEED_REGEX = '<h1 class="title"><i class="fa fa-home"></i> CinemaZ Beta 3.0</h1>'

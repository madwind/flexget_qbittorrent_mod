from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL = 'https://avistaz.to/'
    SUCCEED_REGEX = '<title>AvistaZ Beta 3.0</title>'

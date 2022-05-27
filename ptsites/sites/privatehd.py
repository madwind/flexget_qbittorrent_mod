from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL = 'https://privatehd.to/'
    SUCCEED_REGEX = '<title>PrivateHD Beta 3.0</title>'

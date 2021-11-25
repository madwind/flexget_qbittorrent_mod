from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL = 'https://privatehd.to/'
    SUCCEED_REGEX = '<h1 class="card-header h4">PrivateHD Beta 3.0</h1>'

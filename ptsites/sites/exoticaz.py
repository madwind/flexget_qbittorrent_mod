from ..schema.avistaz import AvistaZ


class MainClass(AvistaZ):
    URL = 'https://exoticaz.to/'
    SUCCEED_REGEX = '<h1 class="card-header h4">ExoticaZ Beta 1.0</h1>'

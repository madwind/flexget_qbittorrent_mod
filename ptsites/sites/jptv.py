from ..schema.site_base import SiteBase
from ..schema.unit3d import Unit3D

# auto_sign_in

URL = 'https://jptv.club/'
SUCCEED_REGEX = '<title>JPTVclub - JPTV for everyone!</title>'


class MainClass(Unit3D):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector

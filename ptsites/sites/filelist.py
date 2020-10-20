from ..schema.ocelot import Ocelot
from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'https://filelist.io/'
SUCCEED_REGEX = 'Hello, <a .+?</a>'


class MainClass(Ocelot):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector

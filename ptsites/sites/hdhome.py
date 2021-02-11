from ..schema.nexusphp import AttendanceHR
from ..schema.site_base import SiteBase


class MainClass(AttendanceHR):
    URL = 'https://hdhome.org/'
    USER_CLASSES = {
        'downloaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [70]
    }

    @classmethod
    def build_reseed(cls, entry, config, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                        '/download\\.php\\?id=\\d+&downhash=.+?(?=")')

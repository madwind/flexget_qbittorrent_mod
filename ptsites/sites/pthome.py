from ..schema.nexusphp import AttendanceHR
from ..schema.site_base import SiteBase


class MainClass(AttendanceHR):
    URL = 'https://www.pthome.net/'
    USER_CLASSES = {
        'downloaded': [1073741824000, 3221225472000],
        'share_ratio': [6, 9],
        'days': [280, 700]
    }

    @classmethod
    def build_reseed(cls, entry, config, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                        '/download\\.php\\?id=\\d+&downhash=.+?(?=")')
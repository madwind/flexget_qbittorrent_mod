from ..schema.nexusphp import AttendanceHR
from ..schema.site_base import SiteBase


class MainClass(AttendanceHR):
    URL = 'https://www.hddolby.com/'
    USER_CLASSES = {
        'downloaded': [1099511627776, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [112, 336]
    }

    @classmethod
    def build_reseed(cls, entry, config, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                        '/download\\.php\\?id=\\d+&downhash=.+?(?=")')

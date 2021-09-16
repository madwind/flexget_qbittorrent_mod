from urllib.parse import urljoin

from ..schema.nexusphp import Visit
# iyuu_auto_reseed
# hd:
#     cookie: '{ cookie }'
from ..schema.site_base import SiteBase


class MainClass(Visit):
    URL = 'https://www.hd.ai/'
    SUCCEED_REGEX = '(?<=<i class="layui-icon layui-icon-username">)</i>.*?(?=</a>)'
    TORRENT_PAGE_URL = urljoin(URL, '/details.php?id={torrent_id}&hit=1')
    DOWNLOAD_URL_REGEX = 'download\\.php\\?hash=.*?id=\\d+'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    @classmethod
    def build_reseed(cls, entry, config, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                        cls.DOWNLOAD_URL_REGEX)

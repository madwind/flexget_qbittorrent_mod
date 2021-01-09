from ..schema.nexusphp import Visit
from ..schema.site_base import SiteBase


# iyuu_auto_reseed
# hd:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'


class MainClass(Visit):
    URL = 'https://www.hd.ai/'
    TORRENT_PAGE_URL = '/details.php?id={}&hit=1'
    SUCCEED_REGEX = '(?<=<i class="layui-icon layui-icon-username">)</i>.*?(?=</a>)'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    @classmethod
    def build_reseed(cls, entry, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                        'download.php\\?hash=.+?uid=\\d+')

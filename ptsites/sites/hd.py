from urllib.parse import urljoin

from ..schema.nexusphp import Visit
from ..utils.net_utils import get_module_name


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
    def reseed_build_schema(cls):
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    @classmethod
    def reseed_build_entry(cls, entry, config, site, passkey, torrent_id):
        cls.reseed_build_entry_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                         cls.DOWNLOAD_URL_REGEX)

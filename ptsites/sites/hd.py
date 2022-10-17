from __future__ import annotations

from typing import Final
from urllib.parse import urljoin

from ..base.reseed import ReseedPage
from ..schema.nexusphp import Visit
from ..utils.net_utils import get_module_name


class MainClass(Visit, ReseedPage):
    URL: Final = 'https://www.hd.ai/'
    SUCCEED_REGEX: Final = '(?<=<i class="layui-icon layui-icon-username">)</i>.*?(?=</a>)'
    TORRENT_PAGE_URL: Final = urljoin(URL, '/details.php?id={torrent_id}&hit=1')
    DOWNLOAD_URL_REGEX: Final = 'download\\.php\\?hash=.*?id=\\d+'
    USER_CLASSES: Final = {
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

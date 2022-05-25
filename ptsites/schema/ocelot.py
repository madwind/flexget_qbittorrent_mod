from abc import ABC

from .private_torrent import PrivateTorrent
from ..utils.value_hanlder import handle_infinite


class Ocelot(PrivateTorrent, ABC):

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'userdetails\.php\?id=(\d+)',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'bar': '#wrapper > div.mainheader > div > div.statusbar > div:nth-child(2)',
                        'table': '.cblock-content'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded.+?([\d.]+ ?[ZEPTGMk]?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded.+?([\d.]+ ?[ZEPTGMk]?B)'
                },
                'share_ratio': {
                    'regex': r'Ratio.+?(Inf\.|[\d.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': (r'Hello.+?(\d+).*?(Inf\.|[\d.]+)', 2)
                },
                'join_date': {
                    'regex': r'Join.date.*?(\d{4}-\d{2}-\d{2})',
                },
                'seeding': {
                    'regex': r'Seeding (\d)+'
                },
                'leeching': None,
                'hr': None
            }
        }

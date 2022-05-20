from .site_base import SiteBase
from ..utils.value_hanlder import handle_infinite


class Ocelot(SiteBase):

    def build_selector(self):
        return {
            'user_id': 'userdetails.php\\?id=(\\d+)',
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
                    'regex': 'Uploaded.+?([\\d.]+ ?[ZEPTGMk]?B)'
                },
                'downloaded': {
                    'regex': 'Downloaded.+?([\\d.]+ ?[ZEPTGMk]?B)'
                },
                'share_ratio': {
                    'regex': 'Ratio.+?(Inf\\.|[\\d.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': ('Hello.+?(\\d+).*?(Inf\\.|[\\d.]+)', 2)
                },
                'join_date': {
                    'regex': 'Join.date.*?(\\d{4}-\\d{2}-\\d{2})',
                },
                'seeding': {
                    'regex': 'Seeding (\\d)+'
                },
                'leeching': None,
                'hr': None
            }
        }

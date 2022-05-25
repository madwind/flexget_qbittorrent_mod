from abc import ABC

from .private_torrent import PrivateTorrent


class Discuz(PrivateTorrent, ABC):
    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'home\.php\?mod=space&amp;uid=(\d+)',
            'detail_sources': {
                'default': {
                    'link': 'home.php?mod=space&amp;uid={}',
                    'elements': {
                        'table': '#ct > div > div.bm > div > div.bm_c.u_profile',
                        'ptconnect_menu': '#ptconnect_menu'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'上传量.*?([\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'downloaded': {
                    'regex': r'下载量.*?([\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': {
                    'regex': r'保种率.*?([\d.,]+)'
                },
                'points': {
                    'regex': r'积分([\d.,]+)金币'
                },
                'join_date': {
                    'regex': r'注册时间(\d{4}-\d{1,2}-\d{1,2})',
                },
                'seeding': {
                    'regex': r'当前做种数 : (\d+)'
                },
                'leeching': {
                    'regex': r'当前下载数 : (\d+)'
                },
                'hr': None,
            }
        }

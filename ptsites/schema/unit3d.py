from abc import ABC

from .private_torrent import PrivateTorrent
from ..utils.value_handler import handle_join_date


class Unit3D(PrivateTorrent, ABC):
    @property
    def details_selector(self) -> dict:
        selector = {
            'user_id': '/users/(.*?)"',
            'detail_sources': {
                'default': {
                    'link': '/users/{}',
                    'elements': {
                        'bar': '#main-content > div.ratio-bar > div > ul',
                        'data_table': '.gradient'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': (r'(上传|Upload).+?([\d.]+.?[ZEPTGMK]?iB)', 2)
                },
                'downloaded': {
                    'regex': (r'(下载|Download).+?([\d.]+.?[ZEPTGMK]?iB)', 2)
                },
                'share_ratio': {
                    'regex': (r'(分享率|Ratio).+?([\d.]+)', 2)
                },
                'points': {
                    'regex': (r'(魔力|BON).+?(\d[\d,. ]*)', 2),
                    'handle': self.handle_points
                },
                'join_date': {
                    'regex': (r'(注册日期|Registration date) (.*?\d{4})', 2),
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': (r'(做种|Seeding).+?(\d+)', 2)
                },
                'leeching': {
                    'regex': (r'(吸血|Leeching).+?(\d+)', 2)
                },
                'hr': {
                    'regex': (r'(警告|Warnings).+?(\d+)', 2)
                }
            }
        }
        return selector

    def handle_points(self, value: str) -> str:
        return value.replace(' ', '')

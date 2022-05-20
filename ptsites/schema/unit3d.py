from .site_base import SiteBase
from ..utils.value_hanlder import handle_join_date


class Unit3D(SiteBase):
    def build_selector(self):
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
                    'regex': ('(上传|Upload).+?([\\d.]+.?[ZEPTGMK]?iB)', 2)
                },
                'downloaded': {
                    'regex': ('(下载|Download).+?([\\d.]+.?[ZEPTGMK]?iB)', 2)
                },
                'share_ratio': {
                    'regex': ('(分享率|Ratio).+?([\\d.]+)', 2)
                },
                'points': {
                    'regex': ('(魔力|BON).+?(\\d[\\d,. ]*)', 2),
                    'handle': self.handle_points
                },
                'join_date': {
                    'regex': ('(注册日期|Registration date) (.*?\\d{4})', 2),
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': ('(做种|Seeding).+?(\\d+)', 2)
                },
                'leeching': {
                    'regex': ('(吸血|Leeching).+?(\\d+)', 2)
                },
                'hr': {
                    'regex': ('(警告|Warnings).+?(\\d+)', 2)
                }
            }
        }
        return selector

    def handle_points(self, value):
        return value.replace(' ', '')

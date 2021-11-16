from dateutil.parser import parse

from .site_base import SiteBase


class Unit3D(SiteBase):

    def get_message(self, entry, config):
        self.get_unit3d_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'user_id': '/users/(.*?)"',
            'detail_sources': {
                'default': {
                    'link': '/users/{}',
                    'elements': {
                        'bar': '#main-content > div.ratio-bar > div > ul',
                        'date_table': '.gradient'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': ('(上传|Upload).+?([\\d.]+ ?[ZEPTGMK]?iB)', 2)
                },
                'downloaded': {
                    'regex': ('(下载|Download).+?([\\d.]+ ?[ZEPTGMK]?iB)', 2)
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
                    'handle': self.handle_join_date
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

    def get_unit3d_message(self, entry, config, messages_url='/mail/inbox'):
        entry['result'] += '(TODO: Message)'

    def handle_points(self, value):
        return value.replace(' ', '')

    def handle_join_date(self, value):
        print(value)
        return parse(value).date()

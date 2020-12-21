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
                    'regex': '上传.+?([\\d.]+ ?[ZEPTGMK]?iB)'
                },
                'downloaded': {
                    'regex': '下载.+?([\\d.]+ ?[ZEPTGMK]?iB)'
                },
                'share_ratio': {
                    'regex': '分享率.+?([\\d.]+)'
                },
                'points': {
                    'regex': '魔力.+?(\\d[\\d,. ]+)',
                    'handle': self.handle_points
                },
                'join_date': {
                    'regex': '注册日期 (.*?\\d{4})',
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': '做种.+?(\\d+)'
                },
                'leeching': {
                    'regex': '吸血.+?(\\d+)'
                },
                'hr': {
                    'regex': '警告.+?(\\d+)'
                }
            }
        }
        return selector

    def get_unit3d_message(self, entry, config, messages_url='/mail/inbox'):
        entry['result'] += '(TODO: Message)'

    def handle_points(self, value):
        return value.replace(' ', '')

    def handle_join_date(self, value):
        return parse(value).date()

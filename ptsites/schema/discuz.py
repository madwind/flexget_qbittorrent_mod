from .site_base import SiteBase


class Discuz(SiteBase):

    def get_message(self, entry, config):
        self.get_discuz_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'user_id': 'home.php\\?mod=space&amp;uid=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': 'home.php?mod=space&amp;uid={}',
                    'elements': {
                        'table': '#ct > div > div.bm > div > div.bm_c.u_profile'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '上传量.*?([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'downloaded': {
                    'regex': '下载量.*?([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': {
                    'regex': '分享率.*?([\\d.,]+)'
                },
                'points': {
                    'regex': '积分([\\d.,]+)金币'
                },
                'join_date': {
                    'regex': '注册时间(\\d{4}-\\d{1,2}-\\d{1,2})',
                },
                'seeding': {
                    'regex': '做种数(\\d+)'
                },
                'leeching': None,
                'hr': None,
            }
        }
        return selector

    def get_discuz_message(self, entry, config, messages_url='/home.php?mod=space&do=pm'):
        entry['result'] += '(TODO: Message)'

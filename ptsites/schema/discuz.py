from .site_base import SiteBase


class Discuz(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

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
                    'regex': '金币([\\d.,]+)'
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
        pass

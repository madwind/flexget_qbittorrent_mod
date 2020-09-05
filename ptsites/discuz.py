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
            'from_page': None,
            'details_link': 'home.php\\?mod=space&amp;uid=\\d+',
            'details_content': {
                'details_bar': None,
                'details_table': '#ct > div > div.bm > div > div.bm_c.u_profile',
            },
            'details': {
                'downloaded': {
                    'regex': '(下载量).*?([\\d.]+ ?[ZEPTGMK]?i?B)',
                    'group': 2,
                },
                'uploaded': {
                    'regex': '(上传量).*?([\\d.]+ ?[ZEPTGMK]?i?B)',
                    'group': 2,
                },
                'share_ratio': {
                    'regex': '(分享率).*?([\\d.,]+)',
                    'group': 2,
                },
                'points': {
                    'regex': '(金币)([\\d.,]+)',
                    'group': 2,
                },
                'seeding': {
                    'regex': '(即时保种数)(\\d+)',
                    'group': 2,
                },
                'leeching': None,
                'hr': None,
            }
        }
        return selector

    def get_discuz_message(self, entry, config, messages_url='/home.php?mod=space&do=pm'):
        pass

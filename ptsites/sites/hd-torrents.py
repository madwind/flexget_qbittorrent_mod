from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'https://hd-torrents.org/'
SUCCEED_REGEX = 'Welcome back, .+?!'


class MainClass(SiteBase):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_hdt_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'body > div.mainmenu > table:nth-child(5)'
                    }
                }
            },
            'details': {
                'downloaded': {
                    'regex': '↓.([\\d.]+ [ZEPTGMK]?iB)'
                },
                'uploaded': {
                    'regex': '↑.([\\d.]+ [ZEPTGMK]?iB)'
                },
                'share_ratio': {
                    'regex': 'Ratio: ([\\d.]+)'
                },
                'points': {
                    'regex': 'Bonus Points:.+?([\\d,.]+)'
                },
                'seeding': {
                    'regex': 'Seeding .+?(\\d+)'
                },
                'leeching': {
                    'regex': 'Leeching .+?(\\d+)'
                },
                'hr': None
            }
        }
        return selector

    def get_hdt_message(self, entry, config, messages_url='/messages.php'):
        pass

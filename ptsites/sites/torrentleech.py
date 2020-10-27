from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'https://www.torrentleech.org/'
SUCCEED_REGEX = '<span class="displayed-username">.+?</span>'


class MainClass(SiteBase):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL + 'none.torrent', SUCCEED_REGEX)

    def sign_in(self, entry, config):
        entry['url'] = URL
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_torrentleech_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'detail_sources': {
                'default': {}
            },
            'details': {
                'downloaded': {
                    'regex': 'Downloaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'uploaded': {
                    'regex': 'Uploaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': 'Ratio.+?(inf\\.|[\\d.]+)',
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': 'TL Points.+?([\\d,.]+)'
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }
        return selector

    def get_torrentleech_message(self, entry, config, messages_url='/messages.php'):
        entry['result'] += '(TODO: Message)'

    def handle_share_ratio(self, value):
        if value == 'inf.':
            return '0'
        else:
            return value

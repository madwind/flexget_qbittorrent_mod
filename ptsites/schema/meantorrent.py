from .site_base import SiteBase


class MeanTorrent(SiteBase):

    def get_message(self, entry, config):
        self.get_meantorrent_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'detail_sources': {
                'default': {
                    'link': '/status/account'
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'uploaded.*?([\\d]+)',
                    'handle': self.handle_suffix
                },
                'downloaded': {
                    'regex': 'downloaded.*?([\\d]+)',
                    'handle': self.handle_suffix
                },
                'share_ratio': None,
                'points': {
                    'regex': 'score.*?([\\d.,]+)'
                },
                'join_date': {
                    'regex': '"created":"(\\d{4}-\\d{2}-\\d{2})'
                },
                'seeding': {
                    'regex': 'seeded.*?(\\d+)'
                },
                'leeching': {
                    'regex': 'leeched.*?(\\d+)'
                },
                'hr': None
            }
        }
        return selector

    def get_meantorrent_message(self, entry, config, messages_url='/messages.php'):
        entry['result'] += '(TODO: Message)'

    def handle_suffix(self, value):
        return str(value) + 'B'

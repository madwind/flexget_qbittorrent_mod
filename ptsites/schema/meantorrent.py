from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from .site_base import SiteBase


class MeanTorrent(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

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
                'downloaded': {
                    'regex': 'downloaded.*?([\\d]+)',
                    'handle': self.handle_suffix
                },
                'uploaded': {
                    'regex': 'uploaded.*?([\\d]+)',
                    'handle': self.handle_suffix
                },
                'share_ratio': None,
                'points': {
                    'regex': 'score.*?([\\d.,]+)'
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
        pass

    def handle_suffix(self, value):
        return str(value) + 'B'

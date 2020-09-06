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
            'from_page': None,
            'details_link': None,
            'details_content': {
                'details_table': 'html',
            },
            'details': {
                'downloaded': {
                    'regex': '(downloaded).*?([\\d]+)',
                    'group': 2,
                    'handle': self.handle_suffix
                },
                'uploaded': {
                    'regex': '(uploaded).*?([\\d]+)',
                    'group': 2,
                    'handle': self.handle_suffix
                },
                'share_ratio': None,
                'points': {
                    'regex': '(score).*?([\\d.,]+)',
                    'group': 2,
                },
                'seeding': {
                    'regex': '(seeded).*?(\\d+)',
                    'group': 2,
                },
                'leeching': {
                    'regex': '(leeched).*?(\\d+)',
                    'group': 2,
                },
                'hr': None,
            }
        }
        return selector

    def get_meantorrent_message(self, entry, config, messages_url='/messages.php'):
        pass

    def handle_suffix(self, value):
        return str(value) + 'B'

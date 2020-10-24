from .site_base import SiteBase


class Ocelot(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_ocelot_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'user_id': None,
            'detail_sources': {
                'default': {
                    'link': None,
                    'elements': {
                        'bar': '#wrapper > div.mainheader > div > div.statusbar > div:nth-child(2)',
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'Uploaded.+?([\\d.]+ ?[ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': 'Downloaded.+?([\\d.]+ ?[ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': 'Ratio.+?([\\d.]+)',
                },
                'points': {
                    'regex': ('Hello.+?(\\d+).*?([\\d.]+)', 2)
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }
        return selector

    def get_ocelot_message(self, entry, config, messages_url='/messages.php'):
        entry['result'] += '(TODO: Message)'

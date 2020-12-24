from .site_base import SiteBase


class Ocelot(SiteBase):

    def get_message(self, entry, config):
        self.get_ocelot_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'user_id': 'userdetails.php\\?id=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'bar': '#wrapper > div.mainheader > div > div.statusbar > div:nth-child(2)',
                        'table': '.cblock-content'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'Uploaded.+?([\\d.]+ ?[ZEPTGMk]?B)'
                },
                'downloaded': {
                    'regex': 'Downloaded.+?([\\d.]+ ?[ZEPTGMk]?B)'
                },
                'share_ratio': {
                    'regex': 'Ratio.+?([\\d.]+)',
                },
                'points': {
                    'regex': ('Hello.+?(\\d+).*?([\\d.]+)', 2)
                },
                'join_date': {
                    'regex': 'Join.date.*?(\\d{4}-\\d{2}-\\d{2})',
                },
                'seeding': {
                    'regex': 'Seeding (\\d)+'
                },
                'leeching': None,
                'hr': None
            }
        }
        return selector

    def get_ocelot_message(self, entry, config, messages_url='/messages.php'):
        entry['result'] += '(TODO: Message)'

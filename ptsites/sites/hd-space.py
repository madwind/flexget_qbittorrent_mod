from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'https://hd-space.org/'
SUCCEED_REGEX = 'Welcome back .*</span> '


class MainClass(SiteBase):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_torrentleech_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'table.lista table.lista'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'UP:.+?([\\d.]+ [ZEPTGMK]B)'
                },
                'downloaded': {
                    'regex': 'DL:.+?([\\d.]+ [ZEPTGMK]B)'
                },
                'share_ratio': {
                    'regex': 'Ratio:.+?(---|[\\d.]+)',
                    'handle': self.handle_inf
                },
                'points': {
                    'regex': 'Bonus:.+?(---|[\\d,.]+)',
                    'handle': self.handle_inf
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }
        return selector

    def get_torrentleech_message(self, entry, config, messages_url='/messages.php'):
        entry['result'] += '(TODO: Message)'

    def handle_inf(self, value):
        if value == '---':
            return '0'
        else:
            return value

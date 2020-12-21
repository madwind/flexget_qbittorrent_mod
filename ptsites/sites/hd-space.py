from ..schema.site_base import SiteBase, Work, SignState


class MainClass(SiteBase):
    URL = 'https://hd-space.org/'

    @classmethod
    def build_workflow(cls):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='Welcome back .*</span> ',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

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

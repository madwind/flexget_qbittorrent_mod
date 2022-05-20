from ..schema.xbtit import XBTIT
from ..utils import net_utils


class MainClass(XBTIT):
    URL = 'https://sportscult.org/'
    SUCCEED_REGEX = 'Welcome back .*?</b>'
    USER_CLASSES = {
        'uploaded': [268435456000],
        'share_ratio': [1.8]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'user_id': 'index.php\\?page=usercp&amp;uid=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/index.php?page=usercp&uid={}',
                    'elements': {
                        'bar': '.b-content table.lista',
                        'table': '#bodyarea #mcol .block-content-r table.lista'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '↑\\s*([\\d.]+ [ZEPTGMK]B)'
                },
                'downloaded': {
                    'regex': '↓\\s*([\\d.]+ [ZEPTGMK]B)'
                },
                'share_ratio': {
                    'regex': 'Ratio (---|[\\d.]+)',
                    'handle': self.handle_inf

                },
                'points': {
                    'regex': 'Bonus (---|[\\d,.]+)',
                    'handle': self.handle_inf
                },
                'join_date': {
                    'regex': 'Joined on:[^\d]+(.*?\d{4})',
                    'handle': self.handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }

        })
        return selector

    def get_message(self, entry, config):
        self.get_XBTIT_message(entry, config,
                               MESSAGES_URL_REGEX='index.php\\?page=usercp&amp;uid=\\d+&amp;do=pm&amp;action=list')

    def handle_inf(self, value):
        if value == '---':
            value = 0
        return value

from ..schema.xbtit import XBTIT
from ..utils.net_utils import NetUtils


class MainClass(XBTIT):
    URL = 'https://hd-space.org/'
    SUCCEED_REGEX = 'Welcome back .*?</span> '
    USER_CLASSES = {
        'uploaded': [2199023255552],
        'share_ratio': [4.25]
    }

    def __init__(self):
        super().__init__()

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'user_id': 'index.php\\?page=usercp&amp;uid=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/index.php?page=usercp&uid={}',
                    'elements': {
                        'bar': 'table.lista table.lista',
                        'table': 'body > div:nth-child(2) > table > tbody > tr > td > table > tbody > tr > td > table > tbody > tr > td > table > tbody > tr > td > table > tbody > tr > td > table:nth-child(9) > tbody > tr:nth-child(2) > td > table:nth-child(2) > tbody > tr > td:nth-child(4) > table'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'UP: ([\\d.]+ [ZEPTGMK]B)'
                },
                'downloaded': {
                    'regex': 'DL:  ([\\d.]+ [ZEPTGMK]B)'
                },
                'share_ratio': {
                    'regex': 'Ratio: (---|[\\d.]+)',
                    'handle': self.handle_inf

                },
                'points': {
                    'regex': 'Bonus: (---|[\\d,.]+)',
                    'handle': self.handle_inf
                },
                'join_date': {
                    'regex': 'Joined on.{5}(.*?\\d{4})',
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

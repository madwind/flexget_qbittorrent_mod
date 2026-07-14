from typing import Final

from ..base.entry import SignInEntry
from ..schema.xbtit import XBTIT
from ..utils import net_utils
from ..utils.value_handler import handle_infinite


class MainClass(XBTIT):
    URL: Final = 'https://hd-space.org/'
    SUCCEED_REGEX: Final = 'Welcome back .*?</span> '
    USER_CLASSES: Final = {
        'uploaded': [2199023255552],
        'share_ratio': [4.25]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
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
                    'handle': handle_infinite

                },
                'points': {
                    'regex': 'Bonus: (---|[\\d,.]+)',
                    'handle': handle_infinite
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

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_XBTIT_message(entry, config,
                               MESSAGES_URL_REGEX='index.php\\?page=usercp&amp;uid=\\d+&amp;do=pm&amp;action=list')

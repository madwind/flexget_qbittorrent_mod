from typing import Final

from ..base.entry import SignInEntry
from ..schema.xbtit import XBTIT
from ..utils import net_utils
from ..utils.value_hanlder import handle_infinite


class MainClass(XBTIT):
    URL: Final = 'https://sportscult.org/'
    SUCCEED_REGEX: Final = 'Welcome back .*?</b>'
    USER_CLASSES: Final = {
        'uploaded': [268435456000],
        'share_ratio': [1.8]
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
                    'handle': handle_infinite

                },
                'points': {
                    'regex': 'Bonus (---|[\\d,.]+)',
                    'handle': handle_infinite
                },
                'join_date': {
                    'regex': r'Joined on:[^\d]+(.*?\d{4})',
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

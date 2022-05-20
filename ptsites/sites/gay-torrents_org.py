from ..schema.xbtit import XBTIT
from ..utils import net_utils
from ..utils.value_hanlder import handle_infinite


class MainClass(XBTIT):
    URL = 'https://gay-torrents.org/'
    SUCCEED_REGEX = 'Logout'
    USER_CLASSES = {
        'uploaded': [268435456000],
        'share_ratio': [2]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'user_id': r'<li><a href="usercp\.php\?uid=(\d+)">My Panel</a>',
            'detail_sources': {
                'default': {
                    'link': '/usercp.php?uid={}',
                    'elements': {
                        'bar': '#user_info',
                        'table': '#main > section > div.block_content.news > section > div.block_content.news > table'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded\s*([\d.]+ ([ZEPTGMK]i)?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded\s*([\d.]+ ([ZEPTGMK]i)?B)'
                },
                'share_ratio': {
                    'regex': r'Ratio\s*(---|[\d.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'Bonus: (---|[\d.]+)',
                    'handle': handle_infinite
                },
                'join_date': {
                    'regex': r'Joined on\s*(\d{2}/\d{2}/\d{4})',
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': r'Active:\s*(\d+)\s*/\s*\d+'
                },
                'leeching': {
                    'regex': r'Active:\s*\d+\s*/\s*(\d+)'
                },
                'hr': None
            }
        })
        return selector

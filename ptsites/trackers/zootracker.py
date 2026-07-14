from typing import Final

from ..base.entry import SignInEntry
from ..schema.nexusphp import Visit
from ..utils.value_handler import handle_infinite


class MainClass(Visit):
    URL: Final = 'https://www.zootracker.vip/'
    @property
    def SUCCEED_REGEX(self) -> str:
        return 'You are logged in as: .*?(?=<)'

    USER_CLASSES: Final = {
        'downloaded': [2147483648000, 1759218604442],
        'share_ratio': [4, 6],
        'days': [70, 1092]
    }

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        pass

    @property
    def details_selector(self) -> dict:
        return {
            'detail_sources': {
                'default': {
                    'link': '/account.php',
                    'elements': {
                        'bar': 'body > table:nth-child(2) > tbody > tr > td:nth-child(2) > table > tbody:nth-child(2) > tr > td > table > tbody:nth-child(2) > tr > td:nth-child(3) > table:nth-child(2) > tbody > tr > td > table:nth-child(2) > tbody > tr > td.bodymain2',
                        'table': '.f-border.comment'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': (r'(Uploaded).+?([\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'downloaded': {
                    'regex': (r'(Downloaded).+?([\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'share_ratio': {
                    'regex': (r'(Ratio).*?(---|∞|Inf\.|无限|無限|[\d,.]+)', 2),
                    'handle': handle_infinite
                },
                'points': None,
                'join_date': {
                    'regex': (r'(Joined).*?(\d{4}-\d{2}-\d{2})', 2),
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }
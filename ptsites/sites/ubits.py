from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils import net_utils
from ..utils.value_handler import size


class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://ubits.club/'
    IGNORE_TITLE = r'H&R\(ID: \d+\) 已达标'
    USER_CLASSES: Final = {
        'downloaded': [size(1.5, 'TiB'), size(4, 'TiB')],
        'share_ratio': [6, 10],
        'points': [1000000, 5000000],
        'days': [175, 420]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': r'做种积分.*?([\d,.]+)'
                }
            }
        })
        return selector

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config, ignore_title=self.IGNORE_TITLE)

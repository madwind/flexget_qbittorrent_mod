from typing import Final

from ..base.entry import SignInEntry
from ..schema.nexusphp import VisitHR
from ..utils import net_utils


class MainClass(VisitHR):
    URL: Final = 'https://ccfbits.org/'
    SUCCEED_REGEX: Final = '欢迎回到CCFBits'
    USER_CLASSES: Final = {
        'uploaded': [5497558138880],
        'downloaded': [322122547200],
        'share_ratio': [2],
        'days': [224]
    }

    def get_nexusphp_messages(self, entry: SignInEntry, config: dict, **kwargs) -> None:
        super().get_nexusphp_messages(entry, config,
                                      unread_elements_selector='tr:nth-child(4) > td > img[alt*="未读"]')

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'body > table:nth-child(2) > tbody > tr > td > table > tbody',
                        'table': 'td.embedded > table'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '上传: ([\\d.]+? [ZEPTGMk]B)',
                    'handle': self.handle_size
                },
                'downloaded': {
                    'regex': '下载: ([\\d.]+? [ZEPTGMk]B)',
                    'handle': self.handle_size
                },
                'points': {
                    'regex': '积分兑换.*?([\\d,.]+)'
                }
            }
        })
        return selector

    def handle_size(self, size: str) -> str:
        return size.upper()

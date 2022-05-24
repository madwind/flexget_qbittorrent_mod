from ..schema.nexusphp import VisitHR
from ..utils import net_utils


def handle_size(size):
    return size.upper()


class MainClass(VisitHR):
    URL = 'https://ccfbits.org/'
    SUCCEED_REGEX = '欢迎回到CCFBits'
    USER_CLASSES = {
        'uploaded': [5497558138880],
        'downloaded': [322122547200],
        'share_ratio': [2],
        'days': [224]
    }

    def get_nexusphp_message(self, entry, config, **kwargs):
        super().get_nexusphp_message(entry, config,
                                     unread_elements_selector='tr:nth-child(4) > td > img[alt*="未读"]')

    def build_selector(self):
        selector = super().build_selector()
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
                    'handle': handle_size
                },
                'downloaded': {
                    'regex': '下载: ([\\d.]+? [ZEPTGMk]B)',
                    'handle': handle_size
                },
                'points': {
                    'regex': '积分兑换.*?([\\d,.]+)'
                }
            }
        })
        return selector

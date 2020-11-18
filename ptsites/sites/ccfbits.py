from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'https://ccfbits.org/'
SUCCEED_REGEX = '欢迎回到CCFBits'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
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

    def handle_size(self, size):
        return size.upper()

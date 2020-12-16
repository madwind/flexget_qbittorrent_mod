from urllib.parse import urljoin

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase

# auto_sign_in

BASE_URL = 'https://hdcity.work/'
DOWNLOAD_BASE_RUL = 'https://assets.hdcity.work/'
URL = urljoin(BASE_URL, '/sign')
SUCCEED_REGEX = '本次签到获得魅力\\d+'

# iyuu_auto_reseed
# hdcity:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'
TORRENT_PAGE_URL = urljoin(BASE_URL, '/t-{}')


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    @staticmethod
    def build_reseed(entry, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, passkey, torrent_id, DOWNLOAD_BASE_RUL, TORRENT_PAGE_URL,
                                        '/dl\\.php.*?(?=")')

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'user_id': None,
            'detail_sources': {
                'default': {
                    'link': None,
                    'elements': {
                        'bar': '#bottomnav > div.button-group',
                        'table': None
                    }
                }
            },
            'details': {
                'downloaded': {
                    'regex': 'arrow_downward([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'uploaded': {
                    'regex': 'arrow_upward([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': None,
                'points': {
                    'regex': '(\\d+)(Bonus|魅力值)'
                },
                'seeding': {
                    'regex': 'play_arrow(\\d+)'
                },
                'leeching': {
                    'regex': 'play_arrow\\d+/(\\d+)'
                },
                'hr': None
            }
        })
        return selector

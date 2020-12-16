from urllib.parse import urljoin

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase

# auto_sign_in

BASE_URL = 'https://hdchina.org/'
URL = urljoin(BASE_URL, '/plugin_sign-in.php?cmd=signin')
SUCCEED_REGEX = '<a class="label label-default" href="#">已签到</a>|{"state":"success","signindays":\\d+,"integral":"?\\d+"?}'
DATA = {
    'csrf': '(?<=x-csrf" content=").*?(?=")',
}

# iyuu_auto_reseed
# hdchina:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'
TORRENT_PAGE_URL = urljoin(BASE_URL, '/details.php?id={}&hit=1')


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX, base_url=BASE_URL)
        entry['data'] = DATA

    @staticmethod
    def build_reseed(entry, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, passkey, torrent_id, BASE_URL, TORRENT_PAGE_URL,
                                        'download\\.php\\?hash=.+?uid=\\d+')

    def sign_in(self, entry, config):
        self.sign_in_by_post_data(entry, config)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#site_header > div.userinfo',
                        'table': '#site_content > div.noraml_box > table'
                    }
                }
            },
            'details': {
                'seeding': {
                    'regex': '\\( (\\d+)　 (\\d+) \\)'
                },
                'leeching': {
                    'regex': ('\\( (\\d+)　 (\\d+) \\)', 2)
                },
                'hr': None
            }
        })
        return selector

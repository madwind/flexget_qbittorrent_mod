import re

import requests
from loguru import logger

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase

# auto_sign_in
BASE_URL = 'https://hdchina.org/'
URL = 'https://hdchina.org/plugin_sign-in.php?cmd=signin'
SUCCEED_REGEX = '<a class="label label-default" href="#">已签到</a>|{"state":"success","signindays":\\d+,"integral":"\\d+"}'
DATA = {
    'csrf': '(?<=x-csrf" content=").*?(?=")',
}

# iyuu_auto_reseed
# hdchina:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'
TORRENT_URL = 'https://hdchina.org/details.php?id={}&hit=1'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX, base_url=BASE_URL)
        entry['data'] = DATA

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        torrent_url = TORRENT_URL.format(torrent_id)
        download_url = None
        try:
            response = requests.get(torrent_url, headers=passkey['headers'], timeout=30)
            if response.status_code == 200:
                re_search = re.search('href="(download\\.php\\?hash=.+?&uid=\\d+)"', response.text)
                if re_search:
                    download_url = re_search.group()
        except Exception as e:
            logger.warning(str(e.args))
        if download_url:
            entry['url'] = 'https://{}/{}'.format(base_url, download_url)
        else:
            entry.reject('download_url is None')

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

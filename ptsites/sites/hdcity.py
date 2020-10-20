import re

import requests
from loguru import logger

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'https://hdcity.work/sign'
SUCCEED_REGEX = '本次签到获得魅力\\d+'

# iyuu_auto_reseed
# hdcity:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'
TORRENT_URL = 'https://hdcity.work/t-{}'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        torrent_url = TORRENT_URL.format(torrent_id)
        download_url = None
        try:
            response = requests.get(torrent_url, headers=passkey['headers'], timeout=30)
            if response.status_code == 200:
                re_search = re.search('https://assets\\.hdcity\\.work/dl\\.php.*?(?=")', response.text)
                if re_search:
                    download_url = re_search.group()
        except Exception as e:
            logger.warning(str(e.args))
        if download_url:
            entry['url'] = download_url
        else:
            entry.reject()

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

import re

import requests
from loguru import logger

from ..site_base import SiteBase
from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://hdcity.work/sign'
TORRENT_URL = 'https://hdcity.work/t-{}'
SUCCEED_REGEX = '本次签到获得魅力\\d+'


# iyuu_auto_reseed
# hdcity:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'

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
                re_search = re.search('https://assets.hdcity.work/dl.php.*?(?=")', response.text)
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
        selector['details_link'] = None
        selector['details_content']['details_bar'] = '#bottomnav > div.button-group'
        selector['details_content']['details_table'] = None

        selector['details']['downloaded'] = {
            'regex': '(arrow_downward)([\\d.]+ ?[ZEPTGMK]?i?B)',
            'group': 2,
        }
        selector['details']['uploaded'] = {
            'regex': '(arrow_upward)([\\d.]+ ?[ZEPTGMK]?i?B)',
            'group': 2,
        }
        selector['details']['share_ratio'] = None
        selector['details']['points'] = {
            'regex': '(\\d+)(Bonus|魅力值 )',
            'group': 1,
        }
        selector['details']['seeding'] = {
            'regex': '(play_arrow)(\\d+)',
            'group': 2,
        }
        selector['details']['leeching'] = {
            'regex': '(play_arrow)(\\d+)/(\\d+)',
            'group': 3,
        }
        return selector

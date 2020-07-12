import re

import requests
from loguru import logger

from ..executor import Executor

# auto_sign_in
URL = 'https://hdcity.city/sign'
TORRENT_URL = 'https://hdcity.city/t-{}'
SUCCEED_REGEX = '本次签到获得魅力\d+'


# iyuu_auto_reseed
# hdcity:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'

class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)

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

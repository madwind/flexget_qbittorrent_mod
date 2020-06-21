import re

import requests
from flexget import plugin
from loguru import logger

from ptsites.executor import Executor

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
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(site_name))
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers

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

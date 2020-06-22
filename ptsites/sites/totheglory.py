from flexget import plugin

from ..executor import Executor

# auto_sign_in
BASE_URL = 'https://totheglory.im/'
URL = 'https://totheglory.im/signed.php'
SUCCEED_REGEX = '<b style="color:green;">已签到</b>|您已连续签到\\d+天，奖励\\d+积分，明天继续签到将获得\\d+积分奖励。'
DATA = {
    'signed_timestamp': '(?<=signed_timestamp: ")\\d{10}',
    'signed_token': '(?<=signed_token: ").*(?=")'
}


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(site_name))
        entry['base_url'] = BASE_URL
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers
        entry['data'] = DATA

    def do_sign_in(self, entry, config):
        self.sign_in_by_post_data(entry, config)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id + '/' + passkey)
        entry['url'] = 'https://{}/{}'.format(base_url, download_page)

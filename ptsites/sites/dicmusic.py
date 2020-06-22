from flexget import plugin

from ..executor import Executor

# auto_sign_in
URL = 'https://dicmusic.club/'


# iyuu_auto_reseed
# dicmusic:
#   authkey: ‘{ authkey }’
#   torrent_pass: '{ torrent_pass }'

class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(site_name))
        entry['url'] = URL
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers

    def get_message(self, entry, config):
        self.get_gazelle_message(entry, config)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=passkey['authkey'],
                                                     torrent_pass=passkey['torrent_pass'])
        entry['url'] = 'https://{}/{}'.format(base_url, download_page)

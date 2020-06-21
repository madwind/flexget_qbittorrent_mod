from flexget import plugin

from ptsites.executor import Executor

# auto_sign_in
URL = 'https://pt.m-team.cc/'
MESSAGE_URL = 'https://pt.m-team.cc/messages.php?action=viewmailbox&box=-2'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(site_name))
        entry['url'] = URL
        entry['message_url'] = MESSAGE_URL
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id + '&passkey=' + passkey)
        entry['url'] = 'https://{}/{}&https=1'.format(base_url, download_page)

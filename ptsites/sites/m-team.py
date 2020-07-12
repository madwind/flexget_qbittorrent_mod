from ..executor import Executor

# auto_sign_in
URL = 'https://pt.m-team.cc/'
SUCCEED_REGEX = '歡迎回來'
MESSAGE_URL = 'https://pt.m-team.cc/messages.php?action=viewmailbox&box=-2'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id + '&passkey=' + passkey)
        entry['url'] = 'https://{}/{}&https=1'.format(base_url, download_page)

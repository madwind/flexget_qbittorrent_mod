from ..gazelle import Gazelle

# auto_sign_in
URL = 'https://dicmusic.club/'
SUCCEED_REGEX = '积分 \\(.*?\\)'


# iyuu_auto_reseed
# dicmusic:
#   authkey: ‘{ authkey }’
#   torrent_pass: '{ torrent_pass }'

class MainClass(Gazelle):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Gazelle.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX)

    @staticmethod
    def build_reseed_entry(entry, base_url, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=passkey['authkey'],
                                                     torrent_pass=passkey['torrent_pass'])
        entry['url'] = 'https://{}/{}'.format(base_url, download_page)

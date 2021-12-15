from urllib.parse import urljoin

from ..schema.site_base import SignState, Work
from ..schema.unit3d import Unit3D


class MainClass(Unit3D):
    URL = 'https://pt.hdpost.top/'

    USER_CLASSES = {
        'uploaded': [10995116277760],
        'days': [365]
    }

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'rsskey': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    @classmethod
    def build_reseed(cls, entry, config, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     rsskey=passkey['rsskey'])
        entry['url'] = urljoin(MainClass.URL, download_page)

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<title>HDPOST - 欢迎来到普斯特</title>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector

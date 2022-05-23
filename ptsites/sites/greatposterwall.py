from urllib.parse import urljoin

from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils import net_utils


class MainClass(Gazelle):
    URL = 'https://greatposterwall.com/'
    USER_CLASSES = {
        'share_ratio': [1.2, 1.2],
        'downloaded': [214748364800, 10995116277760],
        'days': [14, 140]
    }

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'authkey': {'type': 'string'},
                    'torrent_pass': {'type': 'string'}
                },
                "required": ["authkey", "torrent_pass"],
                'additionalProperties': False
            }
        }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=('class="HeaderProfile-name">(.+?)</span>', 1),
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @classmethod
    def build_reseed_entry(cls, entry, config, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=passkey['authkey'],
                                                     torrent_pass=passkey['torrent_pass'])
        entry['url'] = urljoin(MainClass.URL, download_page)

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {'table': 'div.SidebarItemStats.SidebarItem > ul'}
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            },
            'details': {
                'points': None,
            }
        })
        return selector

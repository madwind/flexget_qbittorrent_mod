from urllib.parse import urljoin

from ..base.sign_in import SignState, check_final_state

from ..base.work import Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(Gazelle):
    URL = 'https://greatposterwall.com/'
    USER_CLASSES = {
        'share_ratio': [1.2, 1.2],
        'downloaded': [214748364800, 10995116277760],
        'days': [14, 140]
    }

    @classmethod
    def reseed_build_schema(cls):
        return {
            net_utils.get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'authkey': {'type': 'string'},
                    'torrent_pass': {'type': 'string'}
                },
                "required": ["authkey", "torrent_pass"],
                'additionalProperties': False
            }
        }

    def sign_in_build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[('class="HeaderProfile-name">(.+?)</a>', 1)],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @classmethod
    def reseed_build_entry(cls, entry, config, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=passkey['authkey'],
                                                     torrent_pass=passkey['torrent_pass'])
        entry['url'] = urljoin(MainClass.URL, download_page)

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
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

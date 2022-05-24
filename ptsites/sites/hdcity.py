from urllib.parse import urljoin

from ..base.base import SignState, Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils


class MainClass(NexusPHP):
    URL = 'https://hdcity.work/'
    TORRENT_PAGE_URL = urljoin(URL, '/t-{torrent_id}')
    DOWNLOAD_BASE_URL = 'https://assets.hdcity.work/'
    DOWNLOAD_URL_REGEX = '/dl\\.php.*?(?=")'
    USER_CLASSES = {
        'downloaded': [5497558138880, 43980465111040],
        'share_ratio': [2.5, 4],
        'days': [168, 700]
    }

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/sign',
                method='get',
                succeed_regex=['本次签到获得魅力\\d+'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @classmethod
    def build_reseed_entry(cls, entry, config, site, passkey, torrent_id):
        cls.build_reseed_from_page(entry, config, passkey, torrent_id, cls.DOWNLOAD_BASE_URL, cls.TORRENT_PAGE_URL,
                                   cls.DOWNLOAD_URL_REGEX)

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'user_id': None,
            'detail_sources': {
                'default': {
                    'link': 'https://hdcity.work/userdetails',
                    'elements': {
                        'bar': '#bottomnav > div.button-group',
                        'table': '.text_alt > table > tbody > tr > td:nth-child(2)'
                    }
                }
            },
            'details': {
                'downloaded': {
                    'regex': 'arrow_downward([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'uploaded': {
                    'regex': 'arrow_upward([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': None,
                'points': {
                    'regex': '(\\d+)(Bonus|魅力值)'
                },
                'seeding': {
                    'regex': 'play_arrow(\\d+)'
                },
                'leeching': {
                    'regex': 'play_arrow\\d+/(\\d+)'
                },
                'hr': None
            }
        })
        return selector

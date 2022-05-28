from __future__ import annotations

from typing import Final
from urllib.parse import urljoin

from flexget.entry import Entry

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(NexusPHP):
    URL: Final = 'https://hdcity.work/'
    TORRENT_PAGE_URL: Final = urljoin(URL, '/t-{torrent_id}')
    DOWNLOAD_BASE_URL: Final = 'https://assets.hdcity.work/'
    DOWNLOAD_URL_REGEX: Final = '/dl\\.php.*?(?=")'
    USER_CLASSES: Final = {
        'downloaded': [5497558138880, 43980465111040],
        'share_ratio': [2.5, 4],
        'days': [168, 700]
    }

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/sign',
                method=self.sign_in_by_get,
                succeed_regex=['本次签到获得魅力\\d+'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
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

    @classmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site: dict, passkey: str | dict,
                           torrent_id: str) -> None:
        cls.reseed_build_entry_from_page(entry, config, passkey, torrent_id, cls.DOWNLOAD_BASE_URL,
                                         cls.TORRENT_PAGE_URL,
                                         cls.DOWNLOAD_URL_REGEX)

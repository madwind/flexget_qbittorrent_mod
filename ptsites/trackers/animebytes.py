from __future__ import annotations

from typing import Final
from urllib.parse import urljoin

from flexget.entry import Entry

from ..base.entry import SignInEntry
from ..base.reseed import ReseedCookie
from ..base.sign_in import SignState, check_final_state
from ..base.work import Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.value_handler import handle_infinite


class MainClass(Gazelle, ReseedCookie):
    URL: Final = 'https://animebytes.tv/'
    USER_CLASSES: Final = {
        'downloaded': [214748364800, 1099511627776],
        'share_ratio': [1.2, 1.2],
        'days': [14, 140]
    }

    @classmethod
    def reseed_build_schema(cls) -> dict:
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

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[r'class="username">.*?</a>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'user_id': r'userId: (\d+),',
            'detail_sources': {
                'default': {
                    'link': '/user.php?id={}',
                    'elements': {
                        # Top-nav bonus point balance. Must come before 'bar':
                        # the Tracker Stats panel ends with an unrelated
                        # "Yen per day: ¥0" line the regex would match first.
                        'points': '#yen_count',
                        # The "Tracker Stats" panel, not the "Personal" sidebar box.
                        'bar': '.userstatsright',
                        # The "Details" panel; the join date lives here, in a
                        # different block from Tracker Stats.
                        'join_date_box': '.userstatsleft',
                        # The Gazelle base class also sets a 'table' selector
                        # pointing at the old sidebar layout. dict_merge is a deep
                        # merge, so it must be cleared explicitly or the lookup
                        # fails on the current page.
                        'table': None
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded:\s*([\d.]+ [KMGTPE]?i?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded:\s*([\d.]+ [KMGTPE]?i?B)'
                },
                'share_ratio': {
                    'regex': r'Ratio:\s*([\d,.]+|∞)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'¥([\d,]+)'
                },
                'seeding': {
                    'regex': r'Seeding:\s*(\d+)'
                },
                'leeching': {
                    'regex': r'Leeching:\s*(\d+)'
                },
                'join_date': {
                    # Once tags are stripped there is no '<' left for [^<]+ago
                    # to stop at, so it runs greedily into the "Last Seen: ... ago"
                    # line. Stop at a newline instead.
                    'regex': r'Joined:\s*([^\n<]+ago)',
                },
            }
        })
        return selector

    @classmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site: dict, passkey: str | dict,
                           torrent_id: str) -> None:
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=config['authkey'],
                                                     torrent_pass=config['torrent_pass'])
        entry['url'] = urljoin(MainClass.URL, download_page)

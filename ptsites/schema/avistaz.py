from abc import ABC, abstractmethod

from .private_torrent import PrivateTorrent
from ..base.entry import SignInEntry
from ..base.sign_in import SignState, check_final_state
from ..base.work import Work
from ..utils.value_hanlder import handle_join_date


class AvistaZ(PrivateTorrent, ABC):
    @property
    @abstractmethod
    def SUCCEED_REGEX(self) -> str:
        pass

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[self.SUCCEED_REGEX],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': '/profile/(.*?)"',
            'detail_sources': {
                'default': {
                    'link': '/profile/{}',
                    'elements': {
                        'bar': '.ratio-bar',
                        'date_table': '#content-area'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': (r'([\d.]+ [ZEPTGMK]B).*?([\d.]+ [ZEPTGMK]B).*?([\d.]+)', 1)
                },
                'downloaded': {
                    'regex': (r'([\d.]+ [ZEPTGMK]B).*?([\d.]+ [ZEPTGMK]B).*?([\d.]+)', 2)
                },
                'share_ratio': {
                    'regex': (r'([\d.]+ [ZEPTGMK]B).*?([\d.]+ [ZEPTGMK]B).*?([\d.]+)', 3)
                },
                'points': {
                    'regex': r'Bonus:.([\d.]+)'
                },
                'join_date': {
                    'regex': r'Joined.(.*? \d{4})',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': r'Seeding:.(\d+)'
                },
                'leeching': {
                    'regex': r'Leeching:.(\d+)'
                },
                'hr': {
                    'regex': r'Hit & Run:.(\d+)'
                }
            }
        }

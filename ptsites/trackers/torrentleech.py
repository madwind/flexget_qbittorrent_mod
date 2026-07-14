from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.value_handler import handle_join_date, handle_infinite


class MainClass(PrivateTorrent):
    URL: Final = 'https://www.torrentleech.org/none.torrent'
    USER_CLASSES: Final = {
        'uploaded': [54975581388800],
        'share_ratio': [8],
        'days': [364]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[
                    '<span class="link" style="margin-right: 1em;white-space: nowrap;" onclick="window.location.href=\'.+?\'">.+?</span>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': '/profile/(.*)?/view',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'link': '/profile/{}/view',
                    'elements': {
                        'bar': '.row',
                        'table': '.profileViewTable'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'Uploaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': 'Downloaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': 'ratio-details">(&inf|∞|[\\d.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': 'total-TL-points.+?([\\d,.]+)'
                },
                'join_date': {
                    'regex': 'Registration date</td>.*?<td>(.*?)</td>',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': ('Uploaded.+?([\\d.]+ [ZEPTGMK]?B).*?\\((\\d+)\\)', 2)
                },
                'leeching': {
                    'regex': ('Downloaded.+?([\\d.]+ [ZEPTGMK]?B).*?\\((\\d+)\\)', 2)
                },
                'hr': None
            }
        }

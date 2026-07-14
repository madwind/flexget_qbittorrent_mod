from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.value_handler import handle_join_date, handle_infinite


class MainClass(PrivateTorrent):
    # IPTorrents in list of https://flexget.com/URLRewriters
    URL: Final = 'https://iptorrents.com/download.php/8/none.torrent'
    USER_CLASSES: Final = {
        'uploaded': [53687091200],
        'share_ratio': [1.05],
        'days': [28]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['Log out'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/t']
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': '"/u/(\\d+)"',
            'detail_sources': {
                'default': {
                    'link': '/user.php?u={}',
                    'elements': {
                        'bar': 'div.stats',
                        'table': 'table#body table.t1'
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
                    'regex': r'Ratio (-|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'Bonus Points\s+([\d,.]+)'
                },
                'join_date': {
                    'regex': 'Join date\\s*?(\\d{4}-\\d{2}-\\d{2})',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': 'Seeding([\\d,]+)'
                },
                'leeching': {
                    'regex': 'Leeching([\\d,]+)'
                },
                'hr': None
            }
        }

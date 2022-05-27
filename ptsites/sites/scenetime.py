import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.value_hanlder import handle_infinite


class MainClass(PrivateTorrent):
    URL: Final = 'https://scenetime.com/'
    USER_CLASSES: Final = {
        'uploaded': [32_212_254_720],
        'share_ratio': [1.05],
        'days': [28],
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['Logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
            ),
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': fr'''(?x)(?<= {re.escape('userdetails.php?id=')})
                                (. +?)
                                (?= ")''',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'stats': 'div.startpage > table > tbody > tr > td > table.main',
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'''(?x)(?<= Uploaded)
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMKk] ? B)'''
                },
                'downloaded': {
                    'regex': r'''(?x)(?<= Downloaded)
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMKk] ? B)'''
                },
                'share_ratio': {
                    'regex': r'''(?x)(?<= Share\ Ratio)
                                    (Inf. | [\d,.] +)''',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'''(?x)(?<= Bonus\ Points)
                                    ([\d,.] +)'''
                },
                'join_date': {
                    'regex': r'''(?x)(?<= Join Date)
                                    (\d {4} - \d {2} - \d {2})''',
                },
                'seeding': {
                    'regex': r'''(?x)(?<= Seeding \s)
                                    ([\d,] +)'''
                },
                'leeching': {
                    'regex': r'''(?x)(?<= Leeching \s)
                                    ([\d,] +)'''
                },
                'hr': {
                    'regex': r'''(?x)(?<= Hit\ &\ Runs \s)
                                    ([\d,] +)'''
                },
            }
        }

import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.value_hanlder import handle_join_date


class MainClass(PrivateTorrent):
    URL: Final = 'https://bitsexy.org/'
    USER_CLASSES: Final = {
        'uploaded': [536_870_912_000],
        'share_ratio': [3.05],
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
                                (?= ')''',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'stats': '#wrapper > div.mainheader > div > div.statusbar > div:nth-child(2) > div:nth-child(4)',
                        'table': '#maincolumn > div.cblock-content > div > table:nth-child(4)',
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
                    'regex': r'''(?x)(?<= Ratio )
                                    ([\d,.] +)'''
                },
                'points': {
                    'regex': r'''(?x)(?<= Karma\ points)
                                    ([\d,.] +)'''
                },
                'join_date': {
                    'regex': r'''(?x)(?<= Join date)
                                    ((\w + \ ) {2}
                                    \w +)''',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': r'''(?x)(?<= Seeding:\ )
                                    ([\d,] +)'''
                },
                'leeching': {
                    'regex': r'''(?x)(?<= Leeching:\ )
                                    ([\d,] +)'''
                },
                'hr': None,
            }
        }

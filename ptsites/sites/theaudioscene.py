from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent


class MainClass(PrivateTorrent):
    URL: Final = 'https://theaudioscene.net/'

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
            'detail_sources': {
                'default': {
                    'elements': {
                        'stats': 'table > tbody > tr:nth-child(1) > td:nth-child(3) > div:nth-child(1)',
                    },
                },
            },
            'details': {
                'uploaded': {
                    'regex': r'''(?x)(?<= Uploaded: )
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMK] B)'''
                },
                'downloaded': {
                    'regex': r'''(?x)(?<= Downloaded: )
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMK] B)'''
                },
                'share_ratio': {
                    'regex': r'''(?x)(?<= Ratio: )
                                    ([\d,.] +)'''
                },
                'points': None,
                'seeding': {
                    'regex': r'''(?x)(?<= Uploading: )
                                    ([\d,] +)'''
                },
                'leeching': {
                    'regex': r'''(?x)(?<= Downloading: )
                                    ([\d,] +)'''
                },
                'hr': None,
            }
        }

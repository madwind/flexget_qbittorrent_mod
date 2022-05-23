import re

from ..schema.site_base import SiteBase, Work, SignState
from ..utils.value_hanlder import handle_join_date


class MainClass(SiteBase):
    URL = 'https://bitsexy.org/'
    USER_CLASSES = {
        'uploaded': [536_870_912_000],
        'share_ratio': [3.05],
        'days': [28],
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['Logout'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
            ),
        ]

    def build_selector(self):
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

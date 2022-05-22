import re

from ..schema.site_base import SiteBase, Work, SignState
from ..utils.value_hanlder import handle_infinite


class MainClass(SiteBase):
    URL = 'https://scenetime.com/'
    USER_CLASSES = {
        'uploaded': [32_212_254_720],
        'share_ratio': [1.05],
        'days': [28],
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=r'Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
            ),
        ]

    def build_selector(self):
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

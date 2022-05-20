import re

from ..schema.site_base import SiteBase
from ..utils.value_hanlder import handle_infinite, handle_join_date


class XBT(SiteBase):
    @classmethod
    def build_sign_in_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'login': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string'},
                            'password': {'type': 'string'}
                        },
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            }
        }

    def build_selector(self):
        return {
            'user_id': f'{re.escape("userdetails.php?id=")}'r"(\d+)'>Profile",
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'stats': '#slidingDiv',
                        'join date': '#general > table > tbody > tr:nth-child(1)'
                    }
                },
            },
            'details': {
                'uploaded': {
                    'regex': r'''(?x)Uploaded
                                    ([\d.] +
                                    ([ZEPTGMK] i) ? B)''',
                },
                'downloaded': {
                    'regex': r'''(?x)Downloaded
                                    ([\d.] +
                                    ([ZEPTGMK] i) ? B)''',
                },
                'share_ratio': {
                    'regex': r'''(?x)Share\ Ratio
                                    \s*
                                    (Inf | [\d,.] +)''',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'''(?x)Bonus\ Points
                                    \s*
                                    ([\d,.] +)'''
                },
                'join_date': {
                    'regex': r'''(?x)Join date
                                    ((\w + \ ) {2} \w +)''',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': r'''(?x)Seeding\ Torrents
                                    \s*
                                    ([\d,] +)'''
                },
                'leeching': {
                    'regex': r'''(?x)Leeching\ Torrents
                                    \s*
                                    ([\d,] +)'''
                },
                'hr': {
                    'regex': r'''(?x)Unsatisfied\ Torrents
                                    \s*
                                    ([\d,] +)'''
                }
            }
        }

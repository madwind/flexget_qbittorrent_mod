import re

from ..schema.site_base import SiteBase, Work, SignState
from ..utils.value_hanlder import handle_join_date, handle_infinite


class MainClass(SiteBase):
    URL = 'https://ssl.bootytape.com/'
    USER_CLASSES = {
        'uploaded': [214748364800],
        'share_ratio': [1],
        'days': [31],
    }

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

    def build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login.php',
                method='login',
                succeed_regex='logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/my.php']
            )
        ]

    def build_login_data(self, login, last_content):
        return {
            'take_login': 1,
            'username': login['username'],
            'password': login['password'],
        }

    def build_selector(self):
        return {
            'user_id': fr'{re.escape("Welcome, <a href=userdetails.php?id=")}(\d+)',
            'detail_sources': {
                'default': {
                    'link': '/userdetails.php?id={}',
                    'elements': {
                        'table': 'body > table.mainouter > tbody > tr:nth-child(2) > td > table:nth-child(12)',
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r"""(?x)Uploaded
                                [\d.] +
                                \ 
                                [ZEPTGMKk] ?
                                B
                                \ 
                                \(
                                ([\d,] +)""",
                    'handle': self.handle_amount_of_data
                },
                'downloaded': {
                    'regex': r"""(?x)Downloaded
                                . *?
                                \(
                                ([\d,] +)""",
                    'handle': self.handle_amount_of_data
                },
                'share_ratio': {
                    'regex': r"""(?x)Share
                                \ 
                                ratio
                                (∞ | [\d,.] +)""",
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r"""(?x)Seed
                                \ 
                                Bonus
                                ([\d,.] +)"""
                },
                'join_date': {
                    'regex': r"""(?x)Join
                                \s
                                date
                                (. +?)
                                \ """,
                    'handle': handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

    def handle_amount_of_data(self, value):
        return value + 'B'

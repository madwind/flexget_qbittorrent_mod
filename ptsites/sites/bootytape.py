import re

from ..base.sign_in import  SignState
from ..base.work import Work
from ..base.sign_in import check_final_state
from ..utils.net_utils import get_module_name
from ..schema.private_torrent import PrivateTorrent
from ..utils.value_hanlder import handle_join_date, handle_infinite


class MainClass(PrivateTorrent):
    URL = 'https://ssl.bootytape.com/'

    USER_CLASSES = {
        'uploaded': [214748364800],
        'share_ratio': [1],
        'days': [31],
    }

    @classmethod
    def sign_in_build_schema(cls):
        return {
            get_module_name(cls): {
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

    def sign_in_build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login.php',
                method=self.sign_in_by_login,
                succeed_regex=['logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/my.php']
            )
        ]

    def sign_in_build_login_data(self, login, last_content):
        return {
            'take_login': 1,
            'username': login['username'],
            'password': login['password'],
        }

    @property
    def details_selector(self) -> dict:
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

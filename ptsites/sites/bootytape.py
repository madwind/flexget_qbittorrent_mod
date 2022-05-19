import re

from dateutil.parser import parse

from ..schema.site_base import SiteBase, Work, SignState


def handle_amount_of_data(value):
    return value + 'B'


def handle_join_date(value):
    return parse(value).date()


def handle_share_ratio(value):
    if value in ['--', '∞']:
        return '0'
    else:
        return value


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
                method='password',
                succeed_regex='logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/my.php']
            )
        ]

    @staticmethod
    def sign_in_data(login, last_content):
        return {
            'take_login': 1,
            'username': login['username'],
            'password': login['password'],
        }

    @staticmethod
    def build_selector():
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
                    'handle': handle_amount_of_data
                },
                'downloaded': {
                    'regex': r"""(?x)Downloaded
                                . *?
                                \(
                                ([\d,] +)""",
                    'handle': handle_amount_of_data
                },
                'share_ratio': {
                    'regex': r"""(?x)Share
                                \ 
                                ratio
                                (∞ | [\d,.] +)""",
                    'handle': handle_share_ratio
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

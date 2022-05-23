import re
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flexget.entry import Entry

from ..schema.site_base import SiteBase, Work, SignState, NetworkState
from ..utils.value_hanlder import handle_infinite


class MainClass(SiteBase):
    URL = 'https://abn.lol/'
    USER_CLASSES = {
        'uploaded': [5368709120000],
        'share_ratio': [3.05]
    }

    @classmethod
    def build_sign_in_schema(cls) -> dict:
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

    def build_login_workflow(self, entry: Entry, config: dict) -> list[Work]:
        return [
            Work(
                url='/Home/Login?ReturnUrl=%2F',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/Home/Login',
                method='login',
                succeed_regex=[r'Déconnexion'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
            )
        ]

    def build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'Username': login['username'],
            'Password': login['password'],
            'RememberMe': ['true', 'false'],
            '__RequestVerificationToken': re.search(
                r'(?<=name="__RequestVerificationToken" type="hidden" value=").*?(?=")', last_content).group(),
        }

    def build_selector(self) -> dict:
        return {
            'detail_sources': {
                'default': {
                    'link': '/User',
                    'elements': {
                        'points': 'div.navbar-collapse.collapse.d-sm-inline-flex > ul:nth-child(6) > li:nth-child(3)',
                        'stats': 'div.row.row-padding > div.col-lg-3 > div:nth-child(2) > div.box-body',
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'''(?x)Upload\ :\ 
                                    ([\d.] + \ [ZEPTGMK] ? o)''',
                    'handle': self.handle_amount_of_data
                },
                'downloaded': {
                    'regex': r'''(?x)Download\ :\ 
                                    ([\d.] + \ [ZEPTGMK] ? o)''',
                    'handle': self.handle_amount_of_data
                },
                'share_ratio': {
                    'regex': r'''(?x)Ratio\ :\ 
                                    (∞ | [\d,.] +)''',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'''(?x)Choco's\ :\ 
                                    ([\d,.] +)'''
                },
                'join_date': {
                    'regex': r'''(?mx)Inscrit\ :\ 
                                    (. +?)
                                    $''',
                    'handle': self.handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

    def handle_amount_of_data(self, value: str) -> str:
        return value.replace('o', 'B')

    def handle_join_date(self, value: str) -> datetime:
        value_split = value.removeprefix('Il y a ').replace('et', '').replace('seconde', 'second') \
            .replace('heure', 'hour').replace('journée', 'day').replace('jours', 'days').replace('semaine', 'week') \
            .replace('mois', 'months').replace('an', 'year').replace('années', 'years').split()
        return datetime.now() - relativedelta(**dict(
            (unit if unit.endswith('s') else f'{unit}s', int(amount)) for amount, unit in
            [value_split[i:i + 2] for i in range(0, len(value_split), 2)]))

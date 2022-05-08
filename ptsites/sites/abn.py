import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_amount_of_data(value):
    return value.replace('o', 'B')


def handle_join_date(value):
    value_split = value.removeprefix('Il y a ').replace('et', '').replace('seconde', 'second') \
        .replace('heure', 'hour').replace('journée', 'day').replace('jours', 'days').replace('semaine', 'week') \
        .replace('mois', 'months').replace('an', 'year').replace('années', 'years').split()
    return datetime.now() - relativedelta(**dict(
        (unit if unit.endswith('s') else f'{unit}s', int(amount)) for amount, unit in
        [value_split[i:i + 2] for i in range(0, len(value_split), 2)]))


def handle_share_ratio(value):
    if value == '∞':
        return '0'
    else:
        return value


def build_selector():
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
                'handle': handle_amount_of_data
            },
            'downloaded': {
                'regex': r'''(?x)Download\ :\ 
                                ([\d.] + \ [ZEPTGMK] ? o)''',
                'handle': handle_amount_of_data
            },
            'share_ratio': {
                'regex': r'''(?x)Ratio\ :\ 
                                (∞ | [\d,.] +)''',
                'handle': handle_share_ratio
            },
            'points': {
                'regex': r'''(?x)Choco's\ :\ 
                                ([\d,.] +)'''
            },
            'join_date': {
                'regex': r'''(?mx)Inscrit\ :\ 
                                (. +?)
                                $''',
                'handle': handle_join_date
            },
            'seeding': None,
            'leeching': None,
            'hr': None
        }
    }


class MainClass(SiteBase):
    URL = 'https://abn.lol/'
    USER_CLASSES = {
        'uploaded': [5368709120000],
        'share_ratio': [3.05]
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

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/Home/Login?ReturnUrl=%2F',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/Home/Login',
                method='password',
                succeed_regex=r'Déconnexion',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
                token_regex=r'''(?x)(?<= name="__RequestVerificationToken"\ type="hidden"\ value=")
                                    . *?
                                    (?= ")'''
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'Username': login['username'],
            'Password': login['password'],
            'RememberMe': ['true', 'false'],
            '__RequestVerificationToken': re.search(work.token_regex, last_content).group(),
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

    def get_message(self, entry, config):
        entry['result'] += '(TODO: Message)'  # TODO: Feature not implemented yet

    def get_details(self, entry, config):
        self.get_details_base(entry, config, build_selector())

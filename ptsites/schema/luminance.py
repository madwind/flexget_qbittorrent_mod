import re

from ..schema.site_base import SiteBase, Work, SignState, NetworkState
from ..utils.value_hanlder import handle_infinite, handle_join_date


class Luminance(SiteBase):
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
                url='/login',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method='login',
                succeed_regex=r'''(?x)Logout | Kilpés''',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/'],
            )
        ]

    def build_selector(self):
        return {
            'user_id': fr'''(?x)(?<= {re.escape('user.php?id=')})
                                (. +?)
                                (?= ")''',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'link': '/user.php?id={}',
                    'elements': {
                        'stats': '#content > div > div.sidebar > div:nth-child(4)',
                        'credits': '#bonusdiv > h4',
                        'connected': '#content > div > div.sidebar > div:nth-child(10)'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'''(?x)(?: Uploaded | Feltöltve):
                                    \ 
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMK] ? i ? B)'''
                },
                'downloaded': {
                    'regex': r'''(?x)(?: Downloaded | Letöltve):
                                    \ 
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMK] ? i ? B)'''
                },
                'share_ratio': {
                    'regex': r'''(?x)(?: Ratio | Arány):\ <. *?>
                                    (∞ | [\d,.] +)''',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'''(?x)(?: Credits | Bónuszpontok):
                                    \s *
                                    ([\d,.] +)'''
                },
                'join_date': {
                    'regex': r'''(?x)(?: Joined | Regisztrált):
                                    . *?
                                    title="
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
                'hr': None
            }
        }

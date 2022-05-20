import re

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


class MainClass(SiteBase):
    URL = 'https://www.myanonamouse.net/'
    USER_CLASSES = {
        'uploaded': [26843545600],
        'share_ratio': [2.0],
        'days': [28]
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
                url='/login.php',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/takelogin.php',
                method='login',
                succeed_regex='Log Out',
                response_urls=['/u/'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                t_regex='<input type="hidden" name="t" value="([^"]+)"',
                a_regex='<input type="hidden" name="a" value="([^"]+)"',
            )
        ]

    def sign_in_by_login(self, entry, config, work, last_content):
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        t = re.search(work.t_regex, last_content).group(1)
        a = re.search(work.a_regex, last_content).group(1)
        data = {
            't': t,
            'a': a,
            'email': login['username'],
            'password': login['password'],
            'rememberMe': 'yes'
        }
        return self._request(entry, 'post', work.url, data=data)

    def get_message(self, entry, config):
        self.get_myanonamouse_message(entry, config)

    def build_selector(self):
        return {
            'user_id': '/u/(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/u/{}',
                    'elements': {
                        'bar': '.mmUserStats ul',
                        'table': 'table.coltable'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'Uploaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': 'Downloaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': 'Share ratio.*?(∞|[\\d,.]+)',
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': 'Bonus:\s+([\\d,.]+)'
                },
                'join_date': {
                    'regex': 'Join date\\s*?(\\d{4}-\\d{2}-\\d{2})',
                    'handle': self.handle_join_date
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }

    def get_myanonamouse_message(self, entry, config, messages_url='/messages.php?action=viewmailbox'):
        entry['result'] += '(TODO: Message)'

from ..schema.site_base import SiteBase, Work, SignState


def build_selector():
    return {
        'detail_sources': {
            'default': {
                'do_not_strip': True,
                'link': '/profile',
                'elements': {
                    'table': '#content > div > div > table:nth-child(1) > tbody > tr:nth-child(3) > td',
                }
            }
        },
        'details': {
            'uploaded': None,
            'downloaded': None,
            'share_ratio': None,
            'points': None,
            'join_date': {
                'regex': r'''(?x)(\d {4} - \d {2} - \d {2})'''
            },
            'seeding': None,
            'leeching': None,
            'hr': None
        }
    }


class MainClass(SiteBase):
    URL = 'https://ninjacentral.co.za/'

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
                method='password',
                succeed_regex='Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'redirect': '',
            'username': login['username'],
            'password': login['password'],
            'rememberme': 'on'
        }
        return self._request(entry, 'post', work.url, data=data)

    def get_message(self, entry, config):
        entry['result'] += '(TODO: Message)'  # TODO: Feature not implemented yet

    def get_details(self, entry, config):
        self.get_details_base(entry, config, build_selector())

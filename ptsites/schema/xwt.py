from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_share_ratio(value):
    if value == '---':
        return '0'
    else:
        return value


def build_selector():
    return {
        'detail_sources': {
            'default': {
                'link': '/browse.php',
                'elements': {
                    'ratio': '#wel-radio',
                    'up': '#wel-radiok',
                    'down': '#wel-radio2',
                    'active': '#wel-radio3'
                }
            }
        },
        'details': {
            'uploaded': {
                'regex': r'Up:\s*([\d.]+ (?i:[ZEPTGMK])B)'
            },
            'downloaded': {
                'regex': r'(?i)Down:\s*([\d.]+ [ZEPTGMK]B)'
            },
            'share_ratio': {
                'regex': r'Ratio:\s*(---|[\d,.]+)',
                'handle': handle_share_ratio
            },
            'points': None,
            'seeding': {
                'regex': r'Active:\s*(\d+)'
            },
            'leeching': {
                'regex': r'Active:\s*\d+\s*(\d+)'
            },
            'hr': None
        }
    }


class XWT(SiteBase):
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
                url='/takelogin.php',
                method='password',
                succeed_regex=r'Top 5 Torrents',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/']
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'username': login['username'],
            'password': login['password'],
            'returnto': '/'
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

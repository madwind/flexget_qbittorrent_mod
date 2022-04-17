import ast

from dateutil.parser import parse

from ..schema.site_base import SiteBase, Work, SignState, NetworkState


def handle_join_date(value):
    return parse(value).date()


def handle_amount_of_data(value):
    return value + 'B'


def build_selector():
    return {
        'detail_sources': {
            'default': {
                'link': '/api/v1/auth',
            },
        },
        'details': {
            'uploaded': {
                'regex': r'"uploaded":(\d+)',
                'handle': handle_amount_of_data
            },
            'downloaded': {
                'regex': r'"downloaded":(\d+)',
                'handle': handle_amount_of_data
            },
            'share_ratio': None,
            'points': None,
            'join_date': {
                'regex': r'"createdAt":"(\d{4}-\d{2}-\d{2})',
                'handle': handle_join_date,
            },
            'seeding': None,
            'leeching': None,
            'hr': None,
        },
    }


class MainClass(SiteBase):
    URL = 'https://milkie.cc/'

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
                            'password': {'type': 'string'},
                        },
                        'additionalProperties': False,
                    },
                },
                'additionalProperties': False,
            },
        }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/api/v1/auth/sessions',
                method='login',
                succeed_regex='{"token":".*"}',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/api/v1/auth/sessions'],
            )
        ]

    def sign_in_by_login(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'email': login['username'],
            'password': login['password'],
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        self.requests.headers.update({'authorization': 'Bearer ' + ast.literal_eval(login_response.text)['token']})
        return login_response

    def get_message(self, entry, config):
        entry['result'] += '(TODO: Message)'  # TODO: Feature not implemented yet

    def get_details(self, entry, config):
        self.get_details_base(entry, config, build_selector())

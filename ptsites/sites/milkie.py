import ast
import json
from urllib.parse import urljoin

from ..schema.site_base import SiteBase, Work, SignState, NetworkState
from ..utils import net_utils


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

    def build_login_workflow(self, entry, config):
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
        if not (login := entry['site_config'].get('login')):
            entry.fail_with_prefix('Login data not found!')
            return
        data = {
            'email': login['username'],
            'password': login['password'],
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        self.requests.headers.update({'authorization': 'Bearer ' + ast.literal_eval(login_response.text)['token']})
        return login_response

    def get_details(self, entry, config):
        link = urljoin(entry['url'], '/api/v1/auth')
        detail_response = self._request(entry, 'get', link)
        network_state = self.check_network_state(entry, link, detail_response)
        if network_state != NetworkState.SUCCEED:
            return
        detail_content = net_utils.decode(detail_response)
        data = json.loads(detail_content)
        entry['details'] = {
            'uploaded': str(data['user']['uploaded']) + 'B',
            'downloaded': str(data['user']['downloaded']) + 'B',
            'share_ratio': data['user']['uploaded'] / data['user']['downloaded'] if data['user']['downloaded'] else 0,
            'points': '*',
            'join_date': data['user']['createdAt'].split('T')[0],
            'seeding': '*',
            'leeching': '*',
            'hr': '*'
        }

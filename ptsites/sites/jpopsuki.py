from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState, NetworkState
from ..utils import net_utils


class MainClass(Gazelle):
    URL = 'https://jpopsuki.eu/'
    USER_CLASSES = {
        'uploaded': [26843545600],
        'share_ratio': [1.05],
        'days': [14]
    }

    @classmethod
    def build_sign_in_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'},
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
                method='login',
                check_state=('network', NetworkState.SUCCEED),
                response_urls=['/index.php'],
            ),
        ]

    def build_login_data(self, login, last_content):
        return {
            'username': login['username'],
            'password': login['password'],
            'keeplogged': 1,
            'login': 'Log In!',
        }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['JPopsuki 2.0'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'user_id': 'user.php\\?id=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/user.php?id={}',
                    'elements': {
                        'table': '#content > div > div.sidebar > div:nth-last-child(4) > ul',
                        'Community': '#content > div > div.sidebar > div:last-child > ul'

                    }
                }
            }
        })
        return selector

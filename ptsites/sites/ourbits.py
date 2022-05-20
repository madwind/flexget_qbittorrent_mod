from ..schema.nexusphp import AttendanceHR
from ..schema.site_base import Work, NetworkState
from ..utils import google_auth


class MainClass(AttendanceHR):
    URL = 'https://ourbits.club/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [175, 364]
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
                            'password': {'type': 'string'},
                            'secret_key': {'type': 'string'}
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
                method='login',
                check_state=('network', NetworkState.SUCCEED),
                response_urls=['/index.php']
            )
        ]

    def build_login_data(self, login, last_content):
        return {
            '2fa_code': login.get('secret_key') and google_auth.calc(login['secret_key']) or '',
            'trackerssl': 'yes',
            'username': login['username'],
            'password': login['password'],
        }

from ..schema.nexusphp import AttendanceHR
from ..schema.site_base import Work, NetworkState
from ..utils.google_auth import GoogleAuth


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
                method='password',
                check_state=('network', NetworkState.SUCCEED),
                response_urls=['/index.php']
            )
        ]

    @staticmethod
    def sign_in_data(login, last_content):
        return {
            '2fa_code': login.get('secret_key') and GoogleAuth.calc(login['secret_key']) or '',
            'trackerssl': 'yes',
            'username': login['username'],
            'password': login['password'],
        }

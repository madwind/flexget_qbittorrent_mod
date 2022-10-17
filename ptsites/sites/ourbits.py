from typing import Final

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.reseed import ReseedPasskey
from ..base.sign_in import Work
from ..schema.nexusphp import AttendanceHR
from ..utils import google_auth
from ..utils.net_utils import get_module_name


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://ourbits.club/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [175, 364]
    }

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
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

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            '2fa_code': login.get('secret_key') and google_auth.calc(login['secret_key']) or '',
            'trackerssl': 'yes',
            'username': login['username'],
            'password': login['password'],
            'returnto': 'attendance.php'
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/takelogin.php',
                method=self.sign_in_by_login,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                response_urls=['/attendance.php']
            )
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        workflow = super().sign_in_build_workflow(entry, config)
        workflow[0].use_last_content = True
        return workflow

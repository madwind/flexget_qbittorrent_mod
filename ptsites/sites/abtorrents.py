import ast
import hashlib
from urllib.parse import urljoin

from ..schema.site_base import Work, SignState, NetworkState
from ..schema.xbt import XBT


class MainClass(XBT):
    URL = 'https://abtorrents.me/'
    USER_CLASSES = {
        'uploaded': [536870912000],
        'share_ratio': [1.5],
        'days': [90],
    }

    def build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login.php?returnto=%2F',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/simpleCaptcha.php',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/takelogin.php',
                method='password',
                succeed_regex='Logout',
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
        last_content = ast.literal_eval(last_content)
        target = {'light bulb': '44c7285b', 'house': 'b9a403b9', 'musical note': '3a8441da', 'key': '2faefa2b', 'bug':
            'c2ba10a5', 'heart': 'bed5a0e2', 'clock': '99d86267', 'world': 'ededf171'}[last_content['text']]
        for hash in last_content['images']:
            if hashlib.shake_128(self._request(entry, 'get', urljoin(entry['url'], '/simpleCaptcha.php?hash=' + hash))
                                         .content).hexdigest(4) == target:
                break
        data = {
            'username': login['username'],
            'password': login['password'],
            'remember': 1,
            'captchaSelection': hash,
            'submitme': 'X',
            'returnto': '/'
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

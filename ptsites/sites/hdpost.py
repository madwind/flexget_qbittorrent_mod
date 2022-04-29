import re
from urllib.parse import urljoin

from ..schema.site_base import SignState, Work, NetworkState
from ..schema.unit3d import Unit3D


class MainClass(Unit3D):
    URL = 'https://pt.hdpost.top'
    USER_CLASSES = {
        'uploaded': [109951162777600],
        'days': [365]
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

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'rsskey': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    @classmethod
    def build_reseed(cls, entry, config, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id, rsskey=passkey['rsskey'])
        entry['url'] = urljoin(MainClass.URL, download_page)

    def build_login_workflow(self, entry, config):
        return [
            Work(
                url='/login',
                method='get',
                check_state=('network', NetworkState.SUCCEED),
            ),
            Work(
                url='/login',
                method='password',
                check_state=('network', NetworkState.SUCCEED),
                response_urls=[''],
                token_regex=r'(?<=name="_token" value=").+?(?=")',
                captcha_regex=r'(?<=name="_captcha" value=").+?(?=")',
            )
        ]

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<title>HDPOST - 欢迎来到普斯特</title>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        r = re.compile(r'name="(?P<name>.+?)" value="(?P<value>.+?)" />\s*<button type="submit"')
        m = re.search(r, last_content)
        data = {
            '_token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
            '_captcha': re.search(work.captcha_regex, last_content).group(),
            '_username': '',
            m.group('name'): m.group('value'),
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector

import re
from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from ..schema.site_base import SignState, Work, NetworkState
from ..schema.unit3d import Unit3D
from ..utils.net_utils import NetUtils


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
                response_urls=['', '/pages/1'],
                token_regex=r'(?<=name="_token" value=").+?(?=")',
                captcha_regex=r'(?<=name="_captcha" value=").+?(?=")',
            )
        ]

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=('<a class="top-nav__username" href="https://pt.hdpost.top/users/(.*?)">', 1),
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['', '/']
            )
        ]

    def sign_in_by_password(self, entry, config, work, last_content):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        login_page = get_soup(last_content)
        hidden_input = login_page.select_one('#formContent > form > input[type=hidden]:nth-child(7)')
        name = hidden_input.attrs['name']
        value = hidden_input.attrs['value']
        data = {
            '_token': re.search(work.token_regex, last_content).group(),
            'username': login['username'],
            'password': login['password'],
            'remember': 'on',
            '_captcha': re.search(work.captcha_regex, last_content).group(),
            '_username': '',
            name: value,
        }
        login_response = self._request(entry, 'post', work.url, data=data)
        login_network_state = self.check_network_state(entry, work, login_response)
        if login_network_state != NetworkState.SUCCEED:
            return
        return login_response

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'user_id': '/users/(.*?)/',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': 'ul.top-nav__ratio-bar',
                        'header': '.header',
                        'data_table': '.user-info'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '上传.+?([\\d.]+ ?[ZEPTGMK]?iB)'
                },
                'downloaded': {
                    'regex': '下载.+?([\\d.]+ ?[ZEPTGMK]?iB)'
                },
                'share_ratio': {
                    'regex': '分享率.+?([\\d.]+)',
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': '魔力.+?(\\d[\\d,. ]*)',
                    'handle': self.handle_points
                },
                'join_date': {
                    'regex': '注册日期 (.*?\\d{4})',
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': '做种.+?(\\d+)'
                },
                'leeching': {
                    'regex': '吸血.+?(\\d+)'
                },
                'hr': {
                    'regex': '有效.+?(\\d+)'
                }
            }
        })
        return selector

    def handle_share_ratio(self, value):
        if value in ['.']:
            return '0'
        else:
            return value

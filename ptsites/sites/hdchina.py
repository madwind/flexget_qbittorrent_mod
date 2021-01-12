from urllib.parse import urljoin

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SiteBase, Work, SignState
from ..utils.net_utils import NetUtils


# auto_sign_in


# iyuu_auto_reseed
# hdchina:
#   headers:
#     cookie: '{ cookie }'
#     user-agent: '{? headers.user_agent ?}'


class MainClass(NexusPHP):
    URL = 'https://hdchina.org/'
    DATA = {
        'csrf': '(?<=x-csrf" content=").*?(?=")',
    }
    TORRENT_PAGE_URL = urljoin(URL, '/details.php?id={}&hit=1')

    USER_CLASSES = {
        'downloaded': [5497558138880],
        'share_ratio': [8],
        'days': [350]
    }

    @classmethod
    def build_workflow(cls):
        return [
            Work(
                url='/torrents.php',
                method='get',
                succeed_regex='<a class="label label-default" href="#">已签到</a>',
                fail_regex=None,
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/plugin_sign-in.php?cmd=signin',
                method='post',
                data=cls.DATA,
                succeed_regex='{"state":"success","signindays":\\d+,"integral":"?\\d+"?}',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED)
            )
        ]

    @classmethod
    def build_reseed(cls, entry, config, site, passkey, torrent_id):
        SiteBase.build_reseed_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                        'download\\.php\\?hash=.+?uid=\\d+')

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#site_header > div.userinfo',
                        'table': '#site_content > div.noraml_box > table'
                    }
                }
            },
            'details': {
                'seeding': {
                    'regex': '\\( (\\d+)　 (\\d+) \\)'
                },
                'leeching': {
                    'regex': ('\\( (\\d+)　 (\\d+) \\)', 2)
                },
                'hr': None
            }
        })
        return selector

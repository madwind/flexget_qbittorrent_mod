from ..schema.nexusphp import NexusPHP
from ..schema.site_base import Work, SignState
from ..utils import net_utils


class MainClass(NexusPHP):
    URL = 'https://hdchina.org/'
    TORRENT_PAGE_URL = '/details.php?id={torrent_id}&hit=1'
    DOWNLOAD_URL_REGEX = '/download\\.php\\?hash=.*?&uid=\\d+'
    DATA = {
        'csrf': '(?<=x-csrf" content=").*?(?=")',
    }
    USER_CLASSES = {
        'downloaded': [5497558138880],
        'share_ratio': [8],
        'days': [350]
    }

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/torrents.php',
                method='get',
                succeed_regex='<a class="label label-default" href="#">已签到</a>',
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/plugin_sign-in.php?cmd=signin',
                method='post',
                data=self.DATA,
                succeed_regex='{"state":"success","signindays":\\d+,"integral":"?\\d+"?}',
                check_state=('final', SignState.SUCCEED)
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
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
                    'regex': '\\( (\\d+)　 (\\d+).+?\\)'
                },
                'leeching': {
                    'regex': ('\\( (\\d+)　 (\\d+).+?\\)', 2)
                },
                'hr': None
            }
        })
        return selector

    @classmethod
    def build_reseed_entry(cls, entry, config, site, passkey, torrent_id):
        cls.build_reseed_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                   cls.DOWNLOAD_URL_REGEX)

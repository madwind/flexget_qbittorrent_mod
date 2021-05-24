from ..schema.nexusphp import NexusPHP
from ..schema.site_base import Work, SignState
from ..utils.net_utils import NetUtils


# auto_sign_in


# iyuu_auto_reseed
# hdchina:
#     cookie: '{ cookie }'


class MainClass(NexusPHP):
    URL = 'https://hdchina.org/'
    DATA = {
        'csrf': '(?<=x-csrf" content=").*?(?=")',
    }
    USER_CLASSES = {
        'downloaded': [5497558138880],
        'share_ratio': [8],
        'days': [350]
    }

    def build_workflow(self, entry, config):
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
                data=self.DATA,
                succeed_regex='{"state":"success","signindays":\\d+,"integral":"?\\d+"?}',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED)
            )
        ]

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
                    'regex': '\\( (\\d+)　 (\\d+).+?\\)'
                },
                'leeching': {
                    'regex': ('\\( (\\d+)　 (\\d+).+?\\)', 2)
                },
                'hr': None
            }
        })
        return selector

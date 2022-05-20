from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState, Work
from ..utils import net_utils


class MainClass(NexusPHP):
    URL = 'https://www.haidan.video/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [175, 364]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/index.php',
                method='get',
                succeed_regex='(?<=value=")已经打卡(?=")',
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/signin.php',
                method='get',
                succeed_regex='(?<=value=")已经打卡(?=")',
                response_urls=['/signin.php', '/index.php'],
                check_state=('final', SignState.SUCCEED)
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#head > div.top-panel.special-border > div > div:nth-child(2)',
                        'table': 'body > div.mainroute > div.mainpanel.special-border > table > tbody > tr > td > table'
                    }
                }
            },
            'details': {
                'hr': None
            }
        })
        return selector

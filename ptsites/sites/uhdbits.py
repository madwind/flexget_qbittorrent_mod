from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils import net_utils


class MainClass(Gazelle):
    URL = 'https://uhdbits.org/'
    USER_CLASSES = {
        'downloaded': [322122547200],
        'share_ratio': [2.0],
        'days': [56]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<h1 class="hidden">UHDBits</h1>',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'ul#userinfo_stats',
                        'table': 'div.sidebar > div:nth-child(2) > ul'
                    }
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            }
        })
        return selector

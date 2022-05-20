from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils import net_utils


class MainClass(Gazelle):
    URL = 'https://redacted.ch/'
    USER_CLASSES = {
        'uploaded': [536870912000],
        'share_ratio': [0.65],
        'days': [56]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<h1 class="hidden">Redacted</h1>',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {'table': '#content > div > div.sidebar > div:nth-child(1) > ul'}
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            },
            'details': {
                'points': None,
            }
        })
        return selector

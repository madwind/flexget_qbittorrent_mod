from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils import net_utils


class MainClass(Gazelle):
    URL = 'https://www.empornium.is/'
    USER_CLASSES = {
        'uploaded': [107374182400],
        'share_ratio': [1.05],
        'days': [56]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['<h1 class="hidden">Empornium</h1>'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'table.userinfo_stats',
                        'table': '#content > div > div.sidebar > div:nth-child(4) > ul',
                        'community': '#content > div > div.sidebar > div:nth-child(10) > ul'
                    }
                }
            }
        })
        return selector

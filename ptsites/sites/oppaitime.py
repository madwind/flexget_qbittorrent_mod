from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils import net_utils


class MainClass(Gazelle):
    URL = 'https://oppaiti.me/'
    USER_CLASSES = {
        'uploaded': [107374182400],
        'downloaded': [26843545600],
        'share_ratio': [1.1],
        'points': [10000]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<h1 class="hidden">Oppaitime</h1>',
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
                        'table': '#content > div > div.sidebar > div:nth-child(1) > ul',
                        'bp': '#bonus_points'
                    }
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            }
        })
        return selector

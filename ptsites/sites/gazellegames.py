from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState


class MainClass(Gazelle):
    URL = 'https://gazellegames.net/'

    @classmethod
    def build_workflow(cls):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='Welcome, <a.+?</a>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#community_stats > ul:nth-child(3)',
                        'table': '#content > div > div.sidebar > div.box_main_info'
                    }
                }
            },
            'details': {
                'hr': {
                    'regex': 'Hit \'n\' Runs:.+?(\\d+)?'
                },
            }
        })
        return selector

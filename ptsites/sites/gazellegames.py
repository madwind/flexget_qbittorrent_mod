from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils.net_utils import NetUtils


class MainClass(Gazelle):
    URL = 'https://gazellegames.net/'
    USER_CLASSES = {
        'points': [1200, 6000],
    }

    def build_workflow(self, entry, config):
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
        NetUtils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': '#community_stats > ul:nth-child(3)',
                        'table': '#content > div > div.sidebar > div.box_main_info',
                        'join_date': '.nobullet span.time'
                    }
                },
                'achievements': {
                    'link': '/user.php?action=achievements',
                    'elements': {
                        'total_point': '#content > div[class=linkbox]'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': 'Total Points: (\\d+)'
                },
                'hr': {
                    'regex': 'Hit \'n\' Runs">(\\d+)'
                },
            }
        })
        return selector

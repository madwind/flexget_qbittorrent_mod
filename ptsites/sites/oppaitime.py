import datetime
import re

from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils.net_utils import NetUtils


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
        NetUtils.dict_merge(selector, {
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
            },
            'details': {
                'join_date': {
                    'regex': 'Joined: (.*?ago)',
                    'handle': self.handle_join_date
                },
                'points': {
                    'regex': 'Nips:\s+([\\d,.]+)',
                },
                'hr': None
            }
        })
        return selector

    def handle_share_ratio(self, value):
        if value in ['--', '∞']:
            return '0'
        else:
            return value

    def handle_join_date(self, value):
        year_regex = '(\\d+) years?'
        month_regex = '(\\d+) months?'
        week_regex = '(\\d+) weeks?'
        year = 0
        month = 0
        week = 0
        if year_match := re.search(year_regex, value):
            year = int(year_match.group(1))
        if month_match := re.search(month_regex, value):
            month = int(month_match.group(1))
        if week_match := re.search(week_regex, value):
            week = int(week_match.group(1))
        return (datetime.datetime.now() - datetime.timedelta(days=year * 365 + month * 31 + week * 7)).date()

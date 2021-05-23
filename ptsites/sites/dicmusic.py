import datetime
import re
from urllib.parse import urljoin

from ..schema.gazelle import Gazelle
from ..schema.site_base import Work, SignState
from ..utils.net_utils import NetUtils


# iyuu_auto_reseed
# dicmusic:
#   authkey: ‘{ authkey }’
#   torrent_pass: '{ torrent_pass }'


class MainClass(Gazelle):
    URL = 'https://dicmusic.club/'
    USER_CLASSES = {
        'uploaded': [26843545600, 1319413953331],
        'share_ratio': [1.05, 1.05],
        'days': [14, 112]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='积分 \\(.*?\\)',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @staticmethod
    def build_reseed(entry, config, site, passkey, torrent_id):
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=passkey['authkey'],
                                                     torrent_pass=passkey['torrent_pass'])
        entry['url'] = urljoin(MainClass.URL, download_page)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {'table': 'div.box.box_info.box_userinfo_stats > ul'}
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            },
            'details': {
                'join_date': {
                    'regex': '加入时间:(.*?)前',
                    'handle': self.handle_join_date
                },
                'hr': None
            }
        })
        return selector

    def handle_join_date(self, value):
        year_regex = '(\\d+) 年'
        month_regex = '(\\d+) 月'
        week_regex = '(\\d+) 周'
        year = 0
        month = 0
        week = 0
        if year_match := re.search(year_regex, value):
            year = int(year_match.group(1))
        if month_match := re.search(month_regex, value):
            month = int(month_match.group(1))
        if week_match := re.search(week_regex, value):
            week = int(week_match.group(1))
        print(year, month, week)
        return (datetime.datetime.now() - datetime.timedelta(days=year * 365 + month * 31 + week * 7)).date()

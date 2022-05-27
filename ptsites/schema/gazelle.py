import datetime
import re
from abc import ABC
from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from .private_torrent import PrivateTorrent
from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..utils import net_utils
from ..utils.value_hanlder import handle_infinite


class Gazelle(PrivateTorrent, ABC):

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_gazelle_message(entry, config)

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'user\.php\?id=(\d+)',
            'detail_sources': {
                'default': {
                    'link': '/user.php?id={}',
                    'elements': {'table': '#content > div > div.sidebar > div.box.box_info.box_userinfo_stats > ul'}
                }
            },
            'details': {
                'uploaded': {
                    'regex': (r'(Upload|上传量).+?([\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'downloaded': {
                    'regex': (r'(Download|下载量).+?([\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'share_ratio': {
                    'regex': (r'(Ratio|分享率).*?(∞|[\d,.]+)', 2),
                    'handle': handle_infinite
                },
                'points': {
                    'regex': (r'(Gold|积分|Bonus|Credits|Nips).*?([\d,.]+)', 2)
                },
                'join_date': {
                    'regex': ('(Joined|加入时间).*?(.*?)(ago|前)', 2),
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': r'[Ss]eeding.+?([\d,]+)'
                },
                'leeching': {
                    'regex': r'[Ll]eeching.+?([\d,]+)'
                },
                'hr': None
            }
        }

    def get_gazelle_message(self, entry: SignInEntry, config: dict,
                            message_body_selector: str = 'div[id*="message"]') -> None:
        message_url = urljoin(entry['url'], '/inbox.php')
        message_box_response = self.request(entry, 'get', message_url)
        network_state = check_network_state(entry, message_url, message_box_response)
        if network_state != NetworkState.SUCCEED:
            return
        unread_elements = get_soup(net_utils.decode(message_box_response)).select("tr.unreadpm > td > strong > a")
        failed = False
        for unread_element in unread_elements:
            title = unread_element.text
            href = unread_element.get('href')
            message_url = urljoin(message_url, href)
            message_response = self.request(entry, 'get', message_url)
            network_state = check_network_state(entry, message_url, message_response)
            message_body = 'Can not read message body!'
            if network_state != NetworkState.SUCCEED:
                failed = True
            else:
                body_element = get_soup(
                    net_utils.decode(message_response)).select_one(message_body_selector)
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        if failed:
            entry.fail_with_prefix('Can not read message body!')

    def handle_join_date(self, value: str) -> datetime.date:
        year_regex = '(\\d+) (年|years?)'
        month_regex = '(\\d+) (月|months?)'
        week_regex = '(\\d+) (周|weeks?)'
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

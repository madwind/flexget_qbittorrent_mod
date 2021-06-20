from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from .site_base import SiteBase, NetworkState
from ..utils.net_utils import NetUtils


class Gazelle(SiteBase):

    def get_message(self, entry, config):
        self.get_gazelle_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'user_id': 'user.php\\?id=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/user.php?id={}',
                    'elements': {'table': '#content > div > div.sidebar > div.box.box_info.box_userinfo_stats > ul'}
                }
            },
            'details': {
                'uploaded': {
                    'regex': ('(Upload|上传量).+?([\\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'downloaded': {
                    'regex': ('(Download|下载量).+?([\\d.]+ ?[ZEPTGMK]?i?B)', 2)
                },
                'share_ratio': {
                    'regex': ('(Ratio|分享率).*?(∞|[\\d,.]+)', 2),
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': ('(Gold|积分).*?([\\d,.]+)', 2)
                },
                'seeding': {
                    'regex': '[Ss]eeding.+?([\\d,]+)'
                },
                'leeching': {
                    'regex': '[Ll]eeching.+?([\\d,]+)'
                },
                'hr': None
            }
        }
        return selector

    def get_gazelle_message(self, entry, config, message_body_selector='div[id*="message"]'):
        message_url = urljoin(entry['url'], '/inbox.php')
        message_box_response = self._request(entry, 'get', message_url)
        network_state = self.check_network_state(entry, message_url, message_box_response)
        if network_state != NetworkState.SUCCEED:
            return
        unread_elements = get_soup(NetUtils.decode(message_box_response)).select("tr.unreadpm > td > strong > a")
        failed = False
        for unread_element in unread_elements:
            title = unread_element.text
            href = unread_element.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url)
            network_state = self.check_network_state(entry, message_url, message_response)
            message_body = 'Can not read message body!'
            if network_state != NetworkState.SUCCEED:
                failed = True
            else:
                body_element = get_soup(
                    NetUtils.decode(message_response)).select_one(message_body_selector)
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        if failed:
            entry.fail_with_prefix('Can not read message body!')

    def handle_share_ratio(self, value):
        if value in ['∞']:
            return '0'
        else:
            return value

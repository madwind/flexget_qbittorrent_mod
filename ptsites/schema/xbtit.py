import re
from urllib.parse import urljoin

from dateutil.parser import parse
from flexget.utils.soup import get_soup

from ..schema.site_base import SiteBase, Work, SignState, NetworkState
from ..utils import net_utils


class XBTIT(SiteBase):
    SUCCEED_REGEX = None
    USER_CLASSES = {
        'uploaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [70]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=[self.SUCCEED_REGEX],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = {
            'user_id': 'usercp.php\\?uid=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': '/usercp.php?uid={}',
                    'elements': {
                        'bar': 'body > div.mainmenu > table:nth-child(5)',
                        'table': '#CurrentDetailsHideShowTR'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '↑.([\\d.]+ [ZEPTGMK]?iB)'
                },
                'downloaded': {
                    'regex': '↓.([\\d.]+ [ZEPTGMK]?iB)'
                },
                'share_ratio': {
                    'regex': 'Ratio: ([\\d.]+)'
                },
                'points': {
                    'regex': 'Bonus Points:.+?([\\d,.]+)'
                },
                'join_date': {
                    'regex': 'Joined on.*?(\\d{2}/\\d{2}/\\d{4})',
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': 'Seeding (\\d+)'
                },
                'leeching': {
                    'regex': 'Leeching (\\d+)'
                },
                'hr': None
            }
        }
        return selector

    def get_XBTIT_message(self, entry, config, MESSAGES_URL_REGEX='usercp\\.php\\?uid=\\d+&do=pm&action=list'):
        if messages_url_match := re.search(MESSAGES_URL_REGEX, entry['base_content']):
            messages_url = messages_url_match.group()
        else:
            entry.fail_with_prefix('Can not found messages_url.')
            return
        messages_url = urljoin(entry['url'], messages_url)
        message_box_response = self._request(entry, 'get', messages_url)
        network_state = self.check_network_state(entry, messages_url, message_box_response)
        if network_state != NetworkState.SUCCEED:
            entry.fail_with_prefix('Can not read message box! url:{}'.format(messages_url))
            return

        message_elements = get_soup(net_utils.decode(message_box_response)).select(
            'tr > td.lista:nth-child(1)')
        unread_elements = filter(lambda elements: elements.get_text() == 'no', message_elements)
        failed = False
        for unread_element in unread_elements:
            td = unread_element.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            messages_url = urljoin(messages_url, href)
            message_response = self._request(entry, 'get', messages_url)
            network_state = self.check_network_state(entry, [messages_url], message_response)
            if network_state != NetworkState.SUCCEED:
                message_body = 'Can not read message body!'
                failed = True
            else:
                body_element = get_soup(net_utils.decode(message_response)).select_one(
                    '#PrivateMessageHideShowTR > td > table:nth-child(1) > tbody > tr:nth-child(2) > td')
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, messages_url, message_body))
        if failed:
            entry.fail_with_prefix('Can not read message body!')

    def get_message(self, entry, config):
        self.get_XBTIT_message(entry, config)

    def handle_join_date(self, value):
        return parse(value, dayfirst=True).date()

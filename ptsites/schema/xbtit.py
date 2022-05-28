import re
from abc import ABC, abstractmethod
from datetime import date
from urllib.parse import urljoin

from dateutil.parser import parse
from flexget.utils.soup import get_soup

from .private_torrent import PrivateTorrent
from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState, Work
from ..utils import net_utils


class XBTIT(PrivateTorrent, ABC):
    @property
    @abstractmethod
    def SUCCEED_REGEX(self) -> str:
        pass

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=[self.SUCCEED_REGEX],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'usercp\.php\?uid=(\d+)',
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
                    'regex': r'↑.([\d.]+ [ZEPTGMK]?iB)'
                },
                'downloaded': {
                    'regex': r'↓.([\d.]+ [ZEPTGMK]?iB)'
                },
                'share_ratio': {
                    'regex': r'Ratio: ([\d.]+)'
                },
                'points': {
                    'regex': r'Bonus Points:.+?([\d,.]+)'
                },
                'join_date': {
                    'regex': r'Joined on.*?(\d{2}/\d{2}/\d{4})',
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': r'Seeding (\d+)'
                },
                'leeching': {
                    'regex': r'Leeching (\d+)'
                },
                'hr': None
            }
        }

    def get_XBTIT_message(self, entry: SignInEntry, config: dict,
                          MESSAGES_URL_REGEX: str = 'usercp\\.php\\?uid=\\d+&do=pm&action=list') -> None:
        if messages_url_match := re.search(MESSAGES_URL_REGEX, entry['base_content']):
            messages_url = messages_url_match.group()
        else:
            entry.fail_with_prefix('Can not found messages_url.')
            return
        messages_url = urljoin(entry['url'], messages_url)
        message_box_response = self.request(entry, 'get', messages_url)
        network_state = check_network_state(entry, messages_url, message_box_response)
        if network_state != NetworkState.SUCCEED:
            entry.fail_with_prefix(f'Can not read message box! url:{messages_url}')
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
            message_response = self.request(entry, 'get', messages_url)
            network_state = check_network_state(entry, [messages_url], message_response)
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

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_XBTIT_message(entry, config)

    def handle_join_date(self, value: str) -> date:
        return parse(value, dayfirst=True).date()

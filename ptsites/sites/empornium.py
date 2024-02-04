from typing import Final
from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils


class MainClass(Gazelle):
    URL: Final = 'https://www.empornium.sx/'
    USER_CLASSES: Final = {
        'uploaded': [107374182400],
        'share_ratio': [1.05],
        'days': [56]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<h1 class="hidden">Empornium</h1>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
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

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_gazelle_message(entry, config)

    def get_gazelle_message(self, entry: SignInEntry, config: dict,
                            message_body_selector: str = 'div[id*="message"]') -> None:
        message_url = urljoin(entry['url'], '/user/inbox/received')
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

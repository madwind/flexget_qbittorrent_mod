import re
from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from ..schema.site_base import SiteBase

# auto_sign_in
URL = 'https://hd-torrents.org/'
SUCCEED_REGEX = 'Welcome back, .+?!'
MESSAGES_URL_REGEX = 'usercp\\.php\\?uid=\\d+&do=pm&action=list'


class MainClass(SiteBase):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_hdt_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': 'body > div.mainmenu > table:nth-child(5)'
                    }
                }
            },
            'details': {
                'downloaded': {
                    'regex': '↓.([\\d.]+ [ZEPTGMK]?iB)'
                },
                'uploaded': {
                    'regex': '↑.([\\d.]+ [ZEPTGMK]?iB)'
                },
                'share_ratio': {
                    'regex': 'Ratio: ([\\d.]+)'
                },
                'points': {
                    'regex': 'Bonus Points:.+?([\\d,.]+)'
                },
                'seeding': {
                    'regex': 'Seeding .+?(\\d+)'
                },
                'leeching': {
                    'regex': 'Leeching .+?(\\d+)'
                },
                'hr': None
            }
        }
        return selector

    def get_hdt_message(self, entry, config):
        if messages_url_match := re.search(MESSAGES_URL_REGEX, self._decode(entry['base_response'])):
            messages_url = messages_url_match.group()
        else:
            entry.fail_with_prefix('Can not found messages_url.')
            return
        messages_url = urljoin(entry['url'], messages_url)
        message_box_response = self._request(entry, 'get', messages_url)
        net_state = self.check_net_state(entry, message_box_response, messages_url)
        if net_state:
            entry.fail_with_prefix('Can not read message box! url:{}'.format(messages_url))
            return

        message_elements = get_soup(self._decode(message_box_response)).select(
            'tr > td.lista:nth-child(1)')
        unread_elements = filter(lambda elements: elements.get_text() == 'no', message_elements)
        failed = False
        for unread_element in unread_elements:
            td = unread_element.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            messages_url = urljoin(messages_url, href)
            message_response = self._request(entry, 'get', messages_url)
            net_state = self.check_net_state(entry, message_response, messages_url)
            if net_state:
                message_body = 'Can not read message body!'
                failed = True
            else:
                body_element = get_soup(self._decode(message_response)).select_one(
                    '#PrivateMessageHideShowTR > td > table:nth-child(1) > tbody > tr:nth-child(2) > td')
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, messages_url, message_body))
        if failed:
            entry.fail_with_prefix('Can not read message body!')

from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from .site_base import SiteBase


class NexusPHP(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_nexusphp_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'from_page': None,
            'details_link': 'userdetails.php\\?id=\\d+',
            'details_content': {
                'details_bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(1) > span',
                'details_table': '#outer table:last-child',
            },
            'details': {
                'downloaded': {
                    'regex': '(下[载載]量|Downloaded).+?([\\d.]+ ?[ZEPTGMK]?i?B)',
                    'group': 2,
                },
                'uploaded': {
                    'regex': '(上[传傳]量|Uploaded).+?([\\d.]+ ?[ZEPTGMK]?i?B)',
                    'group': 2,
                },
                'share_ratio': {
                    'regex': '(分享率).*?(无限|無限|[\\d.]+)',
                    'group': 2,
                },
                'points': {
                    'regex': '(魔力).*?([\\d,.]+)',
                    'group': 2,
                },
                'seeding': {
                    'regex': '(当前活动|當前活動).*?(\\d+)',
                    'group': 2,
                },
                'leeching': {
                    'regex': '(当前活动|當前活動).*?(\\d+)\\D+(\\d+)',
                    'group': 3,
                },
                'hr': None,
            }
        }
        return selector

    def get_nexusphp_message(self, entry, config, messages_url='/messages.php'):
        message_url = urljoin(entry['url'], messages_url)
        message_box_response = self._request(entry, 'get', message_url, is_message=True)
        net_state = self.check_net_state(entry, message_box_response, message_url, is_message=True)
        if net_state:
            entry['messages'] = entry['messages'] + '\nCan not read message box! url:{}'.format(message_url)
            entry.fail(entry['messages'])
            return

        unread_elements = get_soup(self._decode(message_box_response)).select(
            'td > img[alt*="Unread"]')
        failed = False
        for unread_element in unread_elements:
            td = unread_element.parent.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url, is_message=True)
            net_state = self.check_net_state(entry, message_response, message_url, is_message=True)
            if net_state:
                message_body = 'Can not read message body!'
                failed = True
            else:
                body_element = get_soup(self._decode(message_response)).select_one('td[colspan*="2"]')
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        if failed:
            entry.fail('Can not read message body!')

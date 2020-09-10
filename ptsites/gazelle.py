from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from .site_base import SiteBase


class Gazelle(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_gazelle_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'from_page': None,
            'details_link': 'user.php\\?id=\\d+',
            'details_content': {
                'details_bar': None,
                'details_table': '#content > div > div.sidebar > div.box.box_info.box_userinfo_stats > ul',
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
                    'regex': '(分享率).*?(∞|[\\d.]+)',
                    'group': 2,
                },
                'points': {
                    'regex': '(积分).*?([\\d,.]+)',
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
                'hr': None
            }
        }
        return selector

    def get_gazelle_message(self, entry, config):
        message_url = urljoin(entry['url'], '/inbox.php')
        message_box_response = self._request(entry, 'get', message_url)
        net_state = self.check_net_state(entry, message_box_response, message_url)
        if net_state:
            return
        unread_elements = get_soup(self._decode(message_box_response)).select("tr.unreadpm > td > strong > a")
        failed = False
        for unread_element in unread_elements:
            title = unread_element.text
            href = unread_element.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url)
            net_state = self.check_net_state(entry, message_response, message_url)
            if net_state:
                message_body = 'Can not read message body!'
                failed = True
            else:
                body_element = get_soup(
                    self._decode(message_response)).select_one('div[id*="message"]')
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        if failed:
            entry.fail('Can not read message body!')

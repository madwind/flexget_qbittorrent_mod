from .site_base import SiteBase


class Ocelot(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_ocelot_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'user_id': None,
            'detail_sources': {
                'default': {
                    'link': None,
                    'elements': {
                        'bar': '#wrapper > div.mainheader > div > div.statusbar > div:nth-child(2)',
                    }
                }
            },
            'details': {
                'downloaded': {
                    'regex': 'Uploaded.+?([\\d.]+ ?[ZEPTGMK]?B)'
                },
                'uploaded': {
                    'regex': 'Downloaded.+?([\\d.]+ ?[ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': 'Ratio.+?([\\d.]+)',
                },
                'points': {
                    'regex': ('Hello.+?(\\d+).*?([\\d.]+)', 2)
                },
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        }
        return selector

    def get_ocelot_message(self, entry, config, messages_url='/messages.php'):
        pass
        # message_box_response = self._request(entry, 'get', messages_url)
        # net_state = self.check_net_state(entry, message_box_response, messages_url)
        # if net_state:
        #     return
        # unread_elements = get_soup(self._decode(message_box_response)).select("tr.unreadpm > td > strong > a")
        # failed = False
        # for unread_element in unread_elements:
        #     title = unread_element.text
        #     href = unread_element.get('href')
        #     message_url = urljoin(message_url, href)
        #     message_response = self._request(entry, 'get', message_url)
        #     net_state = self.check_net_state(entry, message_response, message_url)
        #     if net_state:
        #         message_body = 'Can not read message body!'
        #         failed = True
        #     else:
        #         body_element = get_soup(
        #             self._decode(message_response)).select_one('div[id*="message"]')
        #         if body_element:
        #             message_body = body_element.text.strip()
        #     entry['messages'] = entry['messages'] + (
        #         '\nTitle: {}\nLink: {}\n{}'.format(title, message_url, message_body))
        # if failed:
        #     entry.fail_with_prefix('Can not read message body!')

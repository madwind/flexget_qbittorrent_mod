from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from ..schema.site_base import SiteBase
from ..schema.nexusphp import NexusPHP

# auto_sign_in
URL = 'https://www.pttime.org/attendance.php'
SUCCEED_REGEX = '这是您的第 .* 次签到，已连续签到 .* 天，本次签到获得 .* 个魔力值。|您今天已经签到过了，请勿重复刷新。'


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def get_nexusphp_message(self, entry, config, messages_url='/messages.php'):
        message_url = urljoin(entry['url'], messages_url)
        message_box_response = self._request(entry, 'get', message_url)
        net_state = self.check_net_state(entry, message_box_response, message_url)
        if net_state:
            entry.fail_with_prefix('Can not read message box! url:{}'.format(message_url))
            return

        unread_elements = get_soup(self._decode(message_box_response)).select(
            'td > i[alt*="Unread"]')
        failed = False

        for unread_element in unread_elements:
            td = unread_element.parent.nextSibling.nextSibling
            title = td.text
            href = td.a.get('href')
            message_url = urljoin(message_url, href)
            message_response = self._request(entry, 'get', message_url)
            net_state = self.check_net_state(entry, message_response, message_url)
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
            entry.fail_with_prefix('Can not read message body!')

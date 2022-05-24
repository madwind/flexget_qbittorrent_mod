from urllib.parse import urljoin

from flexget.utils.soup import get_soup

from ..base.base import SignState, NetworkState, Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.state_checkers import check_network_state
from ..utils.value_hanlder import handle_infinite


class MainClass(Gazelle):
    URL = 'https://gazellegames.net/'
    API_URL = urljoin(URL, '/api.php')
    MESSAGE_URL = urljoin(URL, '/inbox.php?action=viewconv&id={conv_id}')
    USER_CLASSES = {
        'points': [1200, 6000],
    }

    @classmethod
    def build_sign_in_schema(cls):
        return {
            cls.get_module_name(): {
                cls.get_module_name(): {
                    'type': 'object',
                    'properties': {
                        'cookie': {'type': 'string'},
                        'key': {'type': 'string'},
                        'name': {'type': 'string'}
                    },
                    'additionalProperties': False
                }
            }
        }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['Welcome, <a.+?</a>'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'elements': {
                        'bar': '#community_stats > ul:nth-child(3)',
                        'table': '#content > div > div.sidebar > div.box_main_info',
                        'join_date': '.nobullet span.time'
                    }
                },
                'achievements': {
                    'link': '/user.php?action=achievements',
                    'elements': {
                        'total_point': '#content > div[class=linkbox]'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': 'Total Points: (\\d+)'
                },
                'hr': {
                    'regex': 'Hit \'n\' Runs">(\\d+)'
                },
            }
        })
        return selector

    def get_details(self, entry, config):
        site_config = entry['site_config']
        key = site_config.get('key')
        name = site_config.get('name')
        if not (key and name):
            entry.fail_with_prefix('key or name not found')
            return
        params = {
            'request': 'user',
            'key': key,
            'name': name
        }
        details_response_json = self.get_api_response_json(entry, params)
        if not details_response_json:
            return
        entry['details'] = {
            'uploaded': f'{details_response_json.get("response").get("stats").get("uploaded") or 0} B'.replace(',', ''),
            'downloaded': f'{details_response_json.get("response").get("stats").get("downloaded") or 0} B'.replace(',',
                                                                                                                   ''),
            'share_ratio': handle_infinite(
                str(details_response_json.get('response').get('stats').get('ratio') or 0).replace(',', '')),
            'points': str(details_response_json.get('response').get('achievements').get('totalPoints') or 0).replace(
                ',', ''),
            'seeding': str(details_response_json.get('response').get('community').get('seeding') or 0).replace(',', ''),
            'leeching': str(details_response_json.get('response').get('community').get('leeching') or 0).replace(',',
                                                                                                                 ''),
            'hr': str(details_response_json.get('response').get('personal').get('hnrs') or 0).replace(',', '')
        }

    def get_message(self, entry, config):
        site_config = entry['site_config']
        key = site_config.get('key')
        if not key:
            entry.fail_with_prefix('key not found')
            return
        params = {
            'request': 'inbox',
            'sort': 'unread',
            'key': key
        }

        messages_response_json = self.get_api_response_json(entry, params)
        if not messages_response_json:
            return
        unread_messages = filter(lambda m: m.get('unread'),
                                 messages_response_json.get('response').get('messages'))
        failed = False
        for message in unread_messages:
            title = message.get('subject')
            conv_id = message.get('convId')
            message_url = MainClass.MESSAGE_URL.format(conv_id=conv_id)
            message_response = self.request(entry, 'get', message_url)
            network_state = check_network_state(entry, message_url, message_response)
            message_body = 'Can not read message body!'
            if network_state != NetworkState.SUCCEED:
                failed = True
            else:
                body_element = get_soup(
                    net_utils.decode(message_response)).select_one('.body')
                if body_element:
                    message_body = body_element.text.strip()
            entry['messages'] = entry['messages'] + (
                f'\nTitle: {title}\nLink: {message_url}\n{message_body}')
        if failed:
            entry.fail_with_prefix('Can not read message body!')

    def get_api_response_json(self, entry, params):
        api_response = self.request(entry, 'get', MainClass.API_URL, params=params)
        network_state = check_network_state(entry, api_response.request.url, api_response)
        if network_state != NetworkState.SUCCEED:
            return
        api_response_json = api_response.json()
        if not api_response_json.get('status') == 'success':
            entry.fail_with_prefix(api_response_json)
            return
        return api_response_json

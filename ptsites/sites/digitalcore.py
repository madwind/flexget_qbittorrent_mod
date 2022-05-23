import json
from urllib.parse import urljoin

from ..schema.site_base import SiteBase, Work, SignState, NetworkState
from ..utils import net_utils


class MainClass(SiteBase):
    URL = 'https://digitalcore.club/'
    USER_CLASSES = {
        'uploaded': [1_288_490_188_800],
        'share_ratio': [1.1],
        'days': [210],
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/api/v1/status?timeSinceLastCheck=0',
                method='get',
                succeed_regex=['user'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
            ),
        ]

    def get_details(self, entry, config):
        link = urljoin(entry['url'],
                       '/api/v1/users/{}'.format(self.get_user_id(entry, '"id":(.+?),', entry['base_content'])))
        detail_response = self._request(entry, 'get', link)
        network_state = self.check_network_state(entry, link, detail_response)
        if network_state != NetworkState.SUCCEED:
            return
        detail_content = net_utils.decode(detail_response)
        data = json.loads(detail_content)
        data2 = json.loads(entry['base_content'])
        entry['details'] = {
            'uploaded': str(data['uploaded']) + 'B',
            'downloaded': str(data['downloaded']) + 'B',
            'share_ratio': data['uploaded'] / data['downloaded'],
            'points': data['bonuspoang'],
            'join_date': data['added'].split()[0],  # TODO: timezone not considered
            'seeding': '*',
            'leeching': '*',
            'hr': data2['user']['hnr'],
        }

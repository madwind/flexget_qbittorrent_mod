import json
from typing import Final
from urllib.parse import urljoin

from ..base.entry import SignInEntry
from ..base.request import NetworkState, check_network_state
from ..base.sign_in import SignState, check_final_state
from ..base.work import Work
from ..schema.private_torrent import PrivateTorrent
from ..utils import net_utils


class MainClass(PrivateTorrent):
    URL: Final = 'https://digitalcore.club/'
    USER_CLASSES: Final = {
        'uploaded': [1_288_490_188_800],
        'share_ratio': [1.1],
        'days': [210],
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/api/v1/status?timeSinceLastCheck=0',
                method=self.sign_in_by_get,
                succeed_regex=['user'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
            ),
        ]

    def get_details(self, entry: SignInEntry, config: dict) -> None:
        link = urljoin(entry['url'],
                       '/api/v1/users/{}'.format(self.get_user_id(entry, '"id":(.+?),', entry['base_content'])))
        detail_response = self.request(entry, 'get', link)
        network_state = check_network_state(entry, link, detail_response)
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

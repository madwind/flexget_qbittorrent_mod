import re
from urllib.parse import urljoin

from ..schema.nexusphp import NexusPHP
from ..schema.site_base import SignState, Work, NetworkState
from ..utils import net_utils


class MainClass(NexusPHP):
    URL = 'https://pt.btschool.club/'
    USER_CLASSES = {
        'downloaded': [1099511627776, 10995116277760],
        'share_ratio': [3.05, 4.55],
        'points': [600000, 1000000],
        'days': [280, 700]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/index.php?action=addbonus',
                method='location',
                succeed_regex='欢迎回来',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            ),
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        # 如果是新用户，父类原来的 table selector 会选择到考核信息的 table，导致无法获取到做种积分信息
                        # 这个 selector 也许可以放到父类里，更通用
                        'table': '#outer > table:last-of-type'
                    }
                }
            },
            'details': {
                'points': {
                    'regex': '做种积分: ([\\d.,]+)',
                }
            }
        })
        return selector

    def sign_in_by_location(self, entry, config, work, last_content=None):
        response = self._request(entry, 'get', work.url)
        reload__net_state = self.check_network_state(entry, work.url, response)
        if reload__net_state != NetworkState.SUCCEED:
            return None
        content = net_utils.decode(response)
        location_search = re.search('(?<=window\\.location=).*?(?=;)', content)
        if not location_search:
            return response
        location_url = re.sub('"|\\+| ', '', location_search.group(0))
        work.url = urljoin(MainClass.URL, location_url)
        return self.sign_in_by_get(entry, config, work, last_content=True)

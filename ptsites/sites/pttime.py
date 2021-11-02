from ..schema.nexusphp import VisitHR
from ..utils.net_utils import NetUtils


class MainClass(VisitHR):
    URL = 'https://www.pttime.org/'
    SUCCEED_REGEX = '<a  href="userdetails.php\?id=\\d+" class=.+?><b>.+?</b></a>'
    USER_CLASSES = {
        'downloaded': [3221225472000, 16106127360000],
        'share_ratio': [3.05, 4.55],
        'days': [112, 364]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block',
                        'table': '#outer table.main:last-child'
                    }
                }
            }
        })
        return selector

    def get_nexusphp_message(self, entry, config):
        super(MainClass, self).get_nexusphp_message(entry, config, unread_elements_selector='td > i[alt*="Unread"]')

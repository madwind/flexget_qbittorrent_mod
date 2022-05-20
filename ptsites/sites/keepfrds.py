from ..schema.nexusphp import Visit
from ..utils.net_utils import NetUtils


class MainClass(Visit):
    URL = 'https://pt.keepfrds.com/'
    USER_CLASSES = {
        'downloaded': [1099511627776, 4398046511104],
        'share_ratio': [3.5, 5],
        'points': [640000, 2560000],
        'days': [420, 1050]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(1)'
                    }
                }
            }
        })
        return selector

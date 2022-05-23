from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit):
    URL = 'https://www.joyhd.net/'
    USER_CLASSES = {
        'downloaded': [644245094400, 5368709120000],
        'share_ratio': [4.5, 6],
        'days': [175, 350]
    }

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': '银元.*?([\\d,.]+)'
                }
            }
        })
        return selector

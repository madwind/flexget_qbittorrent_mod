from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit):
    URL = 'https://nanyangpt.com/'
    SUCCEED_REGEX = '魔力豆 \\(.*?\\)'
    USER_CLASSES = {
        'downloaded': [536870912000, 1099511627776],
        'share_ratio': [5.5, 8.5],
        'days': [140, 350]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#userlink > ul > div:nth-child(3)'
                    }
                }
            }
        })
        return selector

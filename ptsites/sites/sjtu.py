from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit):
    URL = 'https://pt.sjtu.edu.cn/'
    SUCCEED_REGEX = '魔力值 \\(\\d+\\)'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': None,
                        'table': 'body > table.mainouter > tbody > tr:nth-child(2) > td > table:nth-child(5) > tbody > tr > td > table > tbody'
                    }
                },
                'extend': {
                    'link': '/viewpeerstatus.php',
                    'elements': {
                        'bar': 'li'
                    },
                    'do_not_strip': True
                }
            }
        })
        return selector

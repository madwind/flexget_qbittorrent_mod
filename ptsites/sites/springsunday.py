from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL = 'https://springsunday.net/'
    USER_CLASSES = {
        'uploaded': [1832519379627, 109951162777600],
        'downloaded': [2199023255552, 109951162777600],
        'share_ratio': [1.2, 2],
        'points': [400000, 2000000],
        'days': [35, 35]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > div:nth-child(1) > span',
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

from ..schema.nexusphp import Visit


class MainClass(Visit):
    URL = 'https://www.joyhd.net/'
    USER_CLASSES = {
        'downloaded': [644245094400, 5368709120000],
        'share_ratio': [4.5, 6],
        'days': [175, 350]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': '银元.*?([\\d,.]+)'
                }
            }
        })
        return selector

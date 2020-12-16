from ..schema.gazelle import Gazelle
from ..schema.site_base import SiteBase

# auto_sign_in

URL = 'https://gazellegames.net/'
SUCCEED_REGEX = 'Welcome, <a.+?</a>'


class MainClass(Gazelle):
    @staticmethod
    def build_sign_in(entry, config):
        SiteBase.build_sign_in_entry(entry, config, URL, SUCCEED_REGEX)

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        self.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#community_stats > ul:nth-child(3)',
                        'table': '#content > div > div.sidebar > div.box_main_info'
                    }
                }
            },
            'details': {
                'hr': {
                    'regex': 'Hit \'n\' Runs:.+?(\\d+)?'
                },
            }
        })
        return selector

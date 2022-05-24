from abc import ABC

from ..base.base import SignState, Work
from ..base.site_base import SiteBase
from ..utils.value_hanlder import handle_join_date


def handle_points(value):
    return value.replace(' ', '')


class AvistaZ(SiteBase, ABC):
    SUCCEED_REGEX = None

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=[self.SUCCEED_REGEX],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        return {
            'user_id': '/profile/(.*?)"',
            'detail_sources': {
                'default': {
                    'link': '/profile/{}',
                    'elements': {
                        'bar': '.ratio-bar',
                        'date_table': '#content-area'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': (r'([\d.]+ [ZEPTGMK]B).*?([\d.]+ [ZEPTGMK]B).*?([\d.]+)', 1)
                },
                'downloaded': {
                    'regex': (r'([\d.]+ [ZEPTGMK]B).*?([\d.]+ [ZEPTGMK]B).*?([\d.]+)', 2)
                },
                'share_ratio': {
                    'regex': (r'([\d.]+ [ZEPTGMK]B).*?([\d.]+ [ZEPTGMK]B).*?([\d.]+)', 3)
                },
                'points': {
                    'regex': r'Bonus:.([\d.]+)'
                },
                'join_date': {
                    'regex': r'Joined.(.*? \d{4})',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': r'Seeding:.(\d+)'
                },
                'leeching': {
                    'regex': r'Leeching:.(\d+)'
                },
                'hr': {
                    'regex': r'Hit & Run:.(\d+)'
                }
            }
        }

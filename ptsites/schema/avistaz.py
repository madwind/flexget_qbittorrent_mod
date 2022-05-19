from .site_base import SiteBase, Work, SignState


class AvistaZ(SiteBase):
    SUCCEED_REGEX = None

    def build_selector(self):
        selector = {
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
                    'regex': ('([\\d.]+ [ZEPTGMK]B).*?([\\d.]+ [ZEPTGMK]B).*?([\\d.]+)', 1)
                },
                'downloaded': {
                    'regex': ('([\\d.]+ [ZEPTGMK]B).*?([\\d.]+ [ZEPTGMK]B).*?([\\d.]+)', 2)
                },
                'share_ratio': {
                    'regex': ('([\\d.]+ [ZEPTGMK]B).*?([\\d.]+ [ZEPTGMK]B).*?([\\d.]+)', 3)
                },
                'points': {
                    'regex': 'Bonus:.([\\d.]+)'
                },
                'join_date': {
                    'regex': 'Joined.(.*? \\d{4})',
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': 'Seeding:.(\\d+)'
                },
                'leeching': {
                    'regex': 'Leeching:.(\\d+)'
                },
                'hr': {
                    'regex': 'Hit & Run:.(\\d+)'
                }
            }
        }
        return selector

    def handle_points(self, value):
        return value.replace(' ', '')

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=self.SUCCEED_REGEX,
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

from ..schema.site_base import SiteBase, Work, SignState
from ..utils.value_hanlder import handle_join_date, handle_infinite


class MainClass(SiteBase):
    URL = 'https://www.torrentleech.org/none.torrent'
    USER_CLASSES = {
        'uploaded': [54975581388800],
        'share_ratio': [8],
        'days': [364]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['<span class="link" style="margin-right: 1em;white-space: nowrap;" onclick="window.location.href=\'.+?\'">.+?</span>'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        return {
            'user_id': '/profile/(.*)?/view',
            'detail_sources': {
                'default': {
                    'do_not_strip': True,
                    'link': '/profile/{}/view',
                    'elements': {
                        'bar': '.row',
                        'table': '.profileViewTable'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': 'Uploaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': 'Downloaded.+?([\\d.]+ [ZEPTGMK]?B)'
                },
                'share_ratio': {
                    'regex': 'ratio-details">(&inf|∞|[\\d.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': 'total-TL-points.+?([\\d,.]+)'
                },
                'join_date': {
                    'regex': 'Registration date</td>.*?<td>(.*?)</td>',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': ('Uploaded.+?([\\d.]+ [ZEPTGMK]?B).*?\\((\\d+)\\)', 2)
                },
                'leeching': {
                    'regex': ('Downloaded.+?([\\d.]+ [ZEPTGMK]?B).*?\\((\\d+)\\)', 2)
                },
                'hr': None
            }
        }

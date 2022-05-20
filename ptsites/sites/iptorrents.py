from ..schema.site_base import SiteBase, Work, SignState
from ..utils.value_hanlder import handle_join_date, handle_infinite


class MainClass(SiteBase):
    # IPTorrents in list of https://flexget.com/URLRewriters
    URL = 'https://iptorrents.com/download.php/8/none.torrent'
    USER_CLASSES = {
        'uploaded': [53687091200],
        'share_ratio': [1.05],
        'days': [28]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='Log out',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/t']
            )
        ]

    def build_selector(self):
        return {
            'user_id': '"/u/(\\d+)"',
            'detail_sources': {
                'default': {
                    'link': '/user.php?u={}',
                    'elements': {
                        'bar': 'div.stats',
                        'table': 'table#body table.t1'
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
                    'regex': r'Ratio (-|[\d,.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': 'Bonus Points\s+([\\d,.]+)'
                },
                'join_date': {
                    'regex': 'Join date\\s*?(\\d{4}-\\d{2}-\\d{2})',
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': 'Seeding([\\d,]+)'
                },
                'leeching': {
                    'regex': 'Leeching([\\d,]+)'
                },
                'hr': None
            }
        }

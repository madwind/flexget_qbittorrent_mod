from dateutil.parser import parse

from ..schema.site_base import SiteBase, Work, SignState


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
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['/t']
            )
        ]

    def get_message(self, entry, config):
        self.get_iptorrents_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

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
                    'handle': self.handle_share_ratio
                },
                'points': {
                    'regex': 'Bonus Points\s+([\\d,.]+)'
                },
                'join_date': {
                    'regex': 'Join date\\s*?(\\d{4}-\\d{2}-\\d{2})',
                    'handle': self.handle_join_date
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

    def get_iptorrents_message(self, entry, config, messages_url='/inbox'):
        entry['result'] += '(TODO: Message)'

    def handle_share_ratio(self, value):
        if value == '-':
            return '0'
        else:
            return value

    def handle_join_date(self, value):
        return parse(value).date()

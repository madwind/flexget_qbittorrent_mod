from urllib.parse import urljoin

from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils


class MainClass(AttendanceHR):
    URL = 'https://audiences.me/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4.5, 5],
        'days': [560, 784]
    }

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(1)',
                    }
                }
            },
            'details': {
                'points': {
                    'regex': '做种积分([\\d.,]+)',
                }
            }
        })
        return selector

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    @classmethod
    def build_reseed_entry(cls, entry, config, site, passkey, torrent_id):
        download_page = f'download.php?id={torrent_id}'
        entry['url'] = urljoin(MainClass.URL, download_page)
        entry['cookie'] = passkey['cookie']

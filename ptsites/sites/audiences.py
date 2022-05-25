from urllib.parse import urljoin

from ..utils.net_utils import get_module_name
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils


class MainClass(AttendanceHR):
    URL = 'https://audiences.me/'
    USER_CLASSES = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4.5, 5],
        'days': [560, 784]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
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
    def reseed_build_schema(cls):
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    @classmethod
    def reseed_build_entry(cls, entry, config: dict, site, passkey, torrent_id):
        download_page = f'download.php?id={torrent_id}'
        entry['url'] = urljoin(MainClass.URL, download_page)
        entry['cookie'] = passkey['cookie']

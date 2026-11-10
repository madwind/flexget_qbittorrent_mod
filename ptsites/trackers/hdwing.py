from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Visit


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://hdwing.org/'

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        selector['detail_sources']['default']['elements'] = {
            'table': '#site_content table.normal_tab',
        }
        selector['details']['seeding'] = {
            'regex': r'当前做种.*?[（(](\d+)个种子',
        }
        selector['details']['leeching'] = {
            'regex': r'当前下载.*?[（(](\d+)个种子',
        }
        return selector

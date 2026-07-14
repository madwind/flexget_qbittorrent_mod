from typing import Final
from urllib.parse import urljoin

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.work import Work
from ..schema.nexusphp import Visit
from ..utils.value_handler import size


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://leaves.red/'
    USER_CLASSES: Final = {
        'downloaded': [size(750, 'GiB'), size(3, 'TiB')],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        entry['extra_msg'] = f' 未签到: {urljoin(self.URL, "/attendance_new.php")}'
        return super().sign_in_build_workflow(entry, config)

from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils


class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://bitporn.eu/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3, 4.55],
        'points': [50000, 500000],
        'days': [224, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=[
                    'You have already attended .* days, Continuous.* days, this time you will get .* bonus.',
                    'Attend got: \\d+'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'points': {
                    'regex': r'Seed points([\d,.]+)'
                },
                'seeding': {
                    'regex': r'Active: (\d+)'
                },
                'leeching': {
                    'regex': r'Active: \d+  (\d+)'
                },
                'hr': {
                    'regex': r'H&R.*?(\d+)'
                }
            }
        })
        return selector

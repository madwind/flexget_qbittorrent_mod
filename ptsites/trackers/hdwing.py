from typing import Final

from ..base.entry import SignInEntry
from ..base.reseed import ReseedPasskey
from ..base.sign_in import SignState, check_final_state, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import Visit


class MainClass(Visit, ReseedPasskey):
    URL: Final = 'https://hdwing.org/'

    @classmethod
    def sign_in_build_entry(cls, entry: SignInEntry, config: dict) -> None:
        super().sign_in_build_entry(entry, config)
        if cookie := entry.get('cookie'):
            entry['cookie'] = '; '.join(
                part.strip() for part in cookie.split(';')
                if part.strip() and part.partition('=')[0].strip().upper() != 'PHPSESSID'
            )

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/torrents.php',
                method=self.sign_in_by_get,
                succeed_regex=[r'<a class="label label-default" href="#">\s*已签到\s*</a>'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/plugin_sign-in.php?cmd=signin',
                method=self.sign_in_by_post,
                data={'csrf': r'(?<=x-csrf" content=")[^"]+'},
                succeed_regex=[r'\{[^{}]*"state"\s*:\s*"success"[^{}]*\}'],
                assert_state=(check_final_state, SignState.SUCCEED),
            ),
        ]

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

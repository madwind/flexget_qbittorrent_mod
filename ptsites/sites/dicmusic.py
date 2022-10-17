from __future__ import annotations

from typing import Final
from urllib.parse import urljoin

from flexget.entry import Entry

from ..base.entry import SignInEntry
from ..base.reseed import Reseed
from ..base.sign_in import SignState
from ..base.sign_in import check_final_state
from ..base.work import Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(Gazelle, Reseed):
    URL: Final = 'https://dicmusic.club/'
    USER_CLASSES: Final = {
        'uploaded': [26843545600, 1319413953331],
        'share_ratio': [1.05, 1.05],
        'days': [14, 112]
    }

    @classmethod
    def reseed_build_schema(cls):
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'authkey': {'type': 'string'},
                    'torrent_pass': {'type': 'string'}
                },
                "required": ["authkey", "torrent_pass"],
                'additionalProperties': False
            }
        }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['积分 \\(.*?\\)'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {'table': 'div.box.box_info.box_userinfo_stats > ul'}
                },
                'extend': {
                    'link': '/ajax.php?action=community_stats&userid={}'
                }
            }
        })
        return selector

    @classmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site: dict, passkey: str | dict,
                           torrent_id: str) -> None:
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=passkey['authkey'],
                                                     torrent_pass=passkey['torrent_pass'])
        entry['url'] = urljoin(MainClass.URL, download_page)

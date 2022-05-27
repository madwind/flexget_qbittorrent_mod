from __future__ import annotations

from typing import Final

from flexget.entry import Entry

from ..base.entry import SignInEntry
from ..base.sign_in import check_sign_in_state, SignState, check_final_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(NexusPHP):
    URL: Final = 'https://hdchina.org/'
    TORRENT_PAGE_URL: Final = '/details.php?id={torrent_id}&hit=1'
    DOWNLOAD_URL_REGEX: Final = '/download\\.php\\?hash=.*?&uid=\\d+'
    DATA: Final = {
        'csrf': '(?<=x-csrf" content=").*?(?=")',
    }
    USER_CLASSES: Final = {
        'downloaded': [5497558138880],
        'share_ratio': [8],
        'days': [350]
    }

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/torrents.php',
                method=self.sign_in_by_get,
                succeed_regex=['<a class="label label-default" href="#">已签到</a>'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True
            ),
            Work(
                url='/plugin_sign-in.php?cmd=signin',
                method=self.sign_in_by_post,
                data=self.DATA,
                succeed_regex=['{"state":"success","signindays":\\d+,"integral":"?\\d+"?}'],
                assert_state=(check_final_state, SignState.SUCCEED)
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#site_header > div.userinfo',
                        'table': '#site_content > div.noraml_box > table'
                    }
                }
            },
            'details': {
                'seeding': {
                    'regex': '\\( (\\d+)　 (\\d+).+?\\)'
                },
                'leeching': {
                    'regex': ('\\( (\\d+)　 (\\d+).+?\\)', 2)
                },
                'hr': None
            }
        })
        return selector

    @classmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site: dict, passkey: str | dict,
                           torrent_id: str) -> None:
        cls.reseed_build_entry_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                         cls.DOWNLOAD_URL_REGEX)

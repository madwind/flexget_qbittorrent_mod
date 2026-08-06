from __future__ import annotations

from typing import Final
from urllib.parse import urljoin

from ..base.entry import SignInEntry
from ..base.reseed import ReseedCookie
from ..base.work import Work
from ..schema.nexusphp import VisitHR
from ..utils import net_utils


class MainClass(VisitHR, ReseedCookie):
    URL: Final = 'https://audiences.me/'
    USER_CLASSES: Final = {
        'downloaded': [2199023255552, 8796093022208],
        'share_ratio': [4.5, 5],
        'points': [1200000, 1800000],
        'days': [560, 784]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        entry['extra_msg'] = f' 未签到: {urljoin(self.URL, "/attendance.php")}'
        return super().sign_in_build_workflow(entry, config)

    @property
    def SUCCEED_REGEX(self) -> str:
        return 'Audiences :: 首页'

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        # Audiences redesigned #info_block into a ".site-userbar" component. The
        # stat labels (上传量/下载量/分享率/做种积分…) are no longer visible text;
        # they now live in data-*/title/aria-label attributes, so the base
        # label-based regexes ("上传量.+?<num>B" etc.) match the wrong numbers.
        # Fix: parse the raw HTML (do_not_strip) and anchor each value on its
        # stable BEM class modifier instead of on the (now-missing) label text.
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    # feed regexes str(element) instead of element.text
                    'do_not_strip': True
                    # 'bar' falls back to the base '#info_block' selector;
                    # 'table' (userdetails.php) is still used for join_date.
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'compact-metric--uploaded.*?<span>\s*([\d.,]+ ?[ZEPTGMK]?i?B)'
                },
                'downloaded': {
                    'regex': r'compact-metric--downloaded.*?<span>\s*([\d.,]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': {
                    # base keeps its handle_infinite via dict_merge
                    'regex': r'compact-metric--ratio.*?<span>\s*(---|∞|Inf\.|无限|無限|[\d,.]+)'
                },
                'points': {
                    # 做种积分 == "seeding-bonus" tile (NOT --bonus, which is 爆米花)
                    'regex': r'compact-metric--seeding-bonus.*?<span>\s*([\d,.]+)'
                },
                'seeding': {
                    'regex': r'compact-metric-inline-link--seeding.*?([\d,.]+)\s*<'
                },
                'leeching': {
                    'regex': r'compact-metric-inline-link--leeching.*?([\d,.]+)\s*<'
                },
                'hr': {
                    # H&R tile shows "x/y/z" (myhr.php); take the first count
                    'regex': r'compact-metric--hr.*?<span>\s*(\d+)'
                }
            }
        })
        return selector

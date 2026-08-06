from __future__ import annotations

from typing import Final
from urllib.parse import urljoin

from flexget.entry import Entry

from ..base.entry import SignInEntry
from ..base.reseed import ReseedCookie
from ..base.sign_in import SignState, check_final_state
from ..base.work import Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.value_handler import handle_infinite

class MainClass(Gazelle, ReseedCookie):
    URL: Final = 'https://animebytes.tv/'
    USER_CLASSES: Final = {
        'downloaded': [214748364800, 1099511627776],
        'share_ratio': [1.2, 1.2],
        'days': [14, 140]
    }

    @classmethod
    def reseed_build_schema(cls) -> dict:
        return {
            net_utils.get_module_name(cls): {
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
                succeed_regex=[r'class="username">.*?</a>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'user_id': r'userId: (\d+),',
            'detail_sources': {
                'default': {
                    'link': '/user.php?id={}',
                    'elements': {
                        # 顶部导航栏当前魔力值余额；要放在 bar 前面，
                        # 因为 Tracker Stats 面板底部还有一行不相关的 "Yen per day: ¥0"，
                        # 顺序反了正则会先撞上那个
                        'points': '#yen_count',
                        # “Tracker Stats” 面板，别再抓到侧边栏 “Personal” 小盒子里的 Raw 数据了
                        'bar': '.userstatsright',
                        # “Details” 面板，加入日期在这里，跟 Tracker Stats 不是同一个区块
                        'join_date_box': '.userstatsleft',
                        # Gazelle 基类默认还带一个 table 选择器(指向早就不存在的旧版侧边栏)，
                        # dict_merge 是深度合并，不显式清掉的话它会一直留着，页面上找不到就报错
                        'table': None
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'Uploaded:\s*([\d.]+ [KMGTPE]?i?B)'
                },
                'downloaded': {
                    'regex': r'Downloaded:\s*([\d.]+ [KMGTPE]?i?B)'
                },
                'share_ratio': {
                    'regex': r'Ratio:\s*([\d,.]+|âˆž)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'¥([\d,]+)'
                },
                'seeding': {
                    'regex': r'Seeding:\s*(\d+)'
                },
                'leeching': {
                    'regex': r'Leeching:\s*(\d+)'
                },
                'join_date': {
                    # 原来的 [^<]+ago 在文本被去标签后没有 < 可以拦截，
                    # 会一路贪婪匹配到 "Last Seen: ... ago" 那行去，改成遇到换行就停
                    'regex': r'Joined:\s*([^\n<]+ago)',
                },
            }
        })
        return selector

    @classmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site: dict, passkey: str | dict,
                           torrent_id: str) -> None:
        download_page = site['download_page'].format(torrent_id=torrent_id,
                                                     authkey=config['authkey'],
                                                     torrent_pass=config['torrent_pass'])
        entry['url'] = urljoin(MainClass.URL, download_page)

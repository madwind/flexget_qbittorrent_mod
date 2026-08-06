import re
from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import SignState, check_final_state
from ..base.work import Work
from ..schema.unit3d import Unit3D
from ..utils import net_utils


class MainClass(Unit3D):
    URL: Final = 'https://eiga.moi/'
    USER_CLASSES: Final = {
        'downloaded': [109951162777600, 439804651110400],
        'days': [365, 730]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['logout'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector

        selector.get('detail_sources', {}).pop('profile', None)
        selector.get('details', {}).pop('join_date', None)

        # Unit3D 基类默认的 user_id 正则 '/users/(.*?)"' 非贪婪匹配到下一个引号为止，
        # 但首页上第一个撞到的 /users/ 链接不一定是纯用户名(比如 "我的发布" 是 /users/Keado/uploads)，
        # 这样会把 "Keado/uploads" 整个当成 user_id，后面拼出来的详情页链接就全错了。
        # 改成遇到 / 或 " 就停，只取用户名本身
        selector['user_id'] = r'/users/([^/"]+)'

        # 锁定顶部数据栏 + 真正的"警告"面板（Unit3D 默认用 .gradient 选择器，
        # 但 eiga.moi 这个皮肤没有这个 class，所以换成用稳定的 wire:name 属性去定位）
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '.top-nav__ratio-bar',
                        'data_table': 'section[wire\\:name="user-warnings"]'
                    }
                }
            }
        })

        # 因为获取到的纯文本没有“上传/下载”等汉字标签，只能通过固定的坑位顺序来提取
        # 匹配顺序: 1上传 -> 2下载 -> 3做种 -> 4吸血 -> [跳过额度] -> 5魔力 -> 6分享率
        # 注意：原来把 ratio-bar 里第 8 个数字(“免费令” Free Leech Token 数量)当成 HR 用了，
        # 这两个是完全不同的统计量，只是凑巧都是 0 才没露馅，现在改成从真正的警告面板里取
        bar_regex = r'([\d.]+\s*[A-Za-z]+)\s+([\d.]+\s*[A-Za-z]+)\s+(\d+)\s+(\d+)\s+[-]?[\d.]+\s*[A-Za-z]+\s+([\d., \u202f\u00a0]+)\s+(Inf|---?|[\d.]+)'

        net_utils.dict_merge(selector, {
            'details': {
                'uploaded': {
                    'regex': (bar_regex, 1),
                    'handle': self.handle_whitespace
                },
                'downloaded': {
                    'regex': (bar_regex, 2),
                    'handle': self.handle_whitespace
                },
                'seeding': {
                    'regex': (bar_regex, 3)
                },
                'leeching': {
                    'regex': (bar_regex, 4)
                },
                'points': {
                    'regex': (bar_regex, 5),
                    'handle': self.handle_points_custom
                },
                'share_ratio': {
                    'regex': (bar_regex, 6)
                },
                'hr': {
                    # 警告面板里是 "Automated (n)"、"Manual (n)"、"Soft deleted (n)" 三个 tab，
                    # 未软删的两类加起来就是当前有效的警告(H&R)数量
                    'regex': r'(Automated \(\d+\).*?Manual \(\d+\))',
                    'handle': self.handle_warnings
                }
            }
        })
        return selector

    def handle_warnings(self, value: str) -> str:
        nums = re.findall(r'\((\d+)\)', value)
        return str(sum(int(n) for n in nums))

    def handle_whitespace(self, value: str) -> str:
        # 数字和单位之间可能是 \xa0(&nbsp;) 之类的特殊空白符，统一换成普通空格
        return re.sub(r'\s+', ' ', value)

    def get_details(self, entry, config):
        super().get_details(entry, config)
        if entry.get('join_date') is None:
            entry['join_date'] = '2023-01-01'  

    def handle_points_custom(self, value):
        if not value:
            return '0'
        # 暴力清洗特殊的 Unicode 空白符，只保留数字和小数点
        return re.sub(r'[^\d.]', '', value)

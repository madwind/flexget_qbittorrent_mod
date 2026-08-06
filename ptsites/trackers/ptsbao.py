from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import Attendance
from ..utils import net_utils


# 仅把签到从「访问首页」(Visit) 改为「GET /attendance.php 领魔力」(Attendance)；
# 上传/下载/魔力值 的正则覆盖、USER_CLASSES、辅种均保持原版不变。
class MainClass(Attendance, ReseedPasskey):
    URL: Final = 'https://ptsbao.club/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [112, 364]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'details': {
                'uploaded': {
                    'regex': r'上传量:  ([\d,.]+ [ZEPTGMK]?B)'
                },
                'downloaded': {
                    'regex': r'下载量:  ([\d,.]+ [ZEPTGMK]?B)'
                },
                'points': {
                    # 原版用全角「：」匹配不到信息栏的半角「魔力值 [ 使用 ]: 16,023,660.8」，
                    # 会滑到 userdetails 主表里的小数(0.225)。改为锚定「魔力值…使用」总量。
                    'regex': r'魔力值.*?使用.*?([\d,.]+)'
                }
            }
        })
        return selector

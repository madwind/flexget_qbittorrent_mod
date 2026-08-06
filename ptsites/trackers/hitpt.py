from typing import Final

from ..base.reseed import ReseedPasskey
from ..schema.nexusphp import AttendanceHR


# 相比原版(Visit)的两处改动：
#   1) 签到：Visit(访问首页) → AttendanceHR(GET /attendance.php 领魔力)；
#   2) 读 H&R：AttendanceHR 会启用基类 hr 正则 H&R.*?(\d+)，
#      对应信息栏「H&R: [ 0/ 0 /10 ]」取第一个数(与项目其它站一致)。
# USER_CLASSES、辅种保持原版不变。
class MainClass(AttendanceHR, ReseedPasskey):
    URL: Final = 'https://www.hitpt.com/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 2199023255552],
        'share_ratio': [3.05, 4.05],
        'days': [56, 350]
    }

from typing import Final
from ..schema.nexusphp import Visit
from ..schema.nexusphp import Attendance
from ..base.reseed import ReseedPasskey

class MainClass(Attendance, Visit, ReseedPasskey):
    # 这里的 URL 必须与网站实际访问地址一致
    URL: Final = 'https://pt.luckpt.de/'
    USER_CLASSES: Final = {
        'downloaded': [1759218604441, 5387606976102],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700],
        'points': [1800000, 5000000]
    }

    def sign_in_build_workflow(self, entry, config):
        workflow = super().sign_in_build_workflow(entry, config)
        if workflow:
            # 覆写为 POST 签到方法
            workflow[0].method = self.sign_in_by_post
            # 给 POST 请求赋值一个空表单字典，防止触发 NoneType 报错
            workflow[0].data = {}
        return workflow

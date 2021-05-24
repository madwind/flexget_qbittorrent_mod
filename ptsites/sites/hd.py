from ..schema.nexusphp import Visit


# iyuu_auto_reseed
# hd:
#     cookie: '{ cookie }'


class MainClass(Visit):
    URL = 'https://www.hd.ai/'
    SUCCEED_REGEX = '(?<=<i class="layui-icon layui-icon-username">)</i>.*?(?=</a>)'
    USER_CLASSES = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

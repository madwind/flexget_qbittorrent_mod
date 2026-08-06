from typing import Final
from ..schema.nexusphp import Visit
from ..utils import net_utils

class MainClass(Visit):
    URL: Final = 'https://zeus.hamsters.space/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [252, 567]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        # 1. 修正数据栏定位：指向顶部用户信息区域
                        'bar': '#header-userinfo',
                        
                        # 2. 修正表格定位：指向 #outer 内部的表格
                        'table': '#outer table'
                    }
                }
            },
            'details': {
                # 上传量：直接定位 ID，通常这个没问题
                'uploaded': {
                    'regex': r'([\d.]+ ?[ZEPTGMK]?i?B)',
                    'selector': '#uploaded'
                },
                
                # 3. 魔力值重点修复：
                # 策略：抓取包含 "魔力值" 文字的父级标签，确保上下文完整
                'points': {
                    'regex': r'魔力值.*?([\d,.]+)',
                    'selector': 'a[href*="mybonus.php"]',
                    'handle': self.handle_points
                },
                
                # 4. 避坑处理：强制不抓取连在一起的做种/吸血数
                'seeding': None,
                'leeching': None,
                'hr': None
            }
        })
        return selector

    def handle_points(self, value):
        # 去除逗号，确保返回纯数字格式 (例如: "224,261.5" -> "224261.5")
        return value.replace(',', '')

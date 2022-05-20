from .site_base import SiteBase


class Discuz(SiteBase):
    def build_selector(self):
        return {
            'user_id': 'home.php\\?mod=space&amp;uid=(\\d+)',
            'detail_sources': {
                'default': {
                    'link': 'home.php?mod=space&amp;uid={}',
                    'elements': {
                        'table': '#ct > div > div.bm > div > div.bm_c.u_profile',
                        'ptconnect_menu': '#ptconnect_menu'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '上传量.*?([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'downloaded': {
                    'regex': '下载量.*?([\\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': {
                    'regex': '保种率.*?([\\d.,]+)'
                },
                'points': {
                    'regex': '积分([\\d.,]+)金币'
                },
                'join_date': {
                    'regex': '注册时间(\\d{4}-\\d{1,2}-\\d{1,2})',
                },
                'seeding': {
                    'regex': '当前做种数 : (\\d+)'
                },
                'leeching': {
                    'regex': '当前下载数 : (\\d+)'
                },
                'hr': None,
            }
        }

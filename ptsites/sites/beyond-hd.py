from ..schema.site_base import SignState, Work
from ..schema.unit3d import Unit3D


# site_config
#    oneurl: 'xxxxxxxx'
#    cookie: 'xxxxxxxx'

# Choose between oneurl or cookie 
# If oneurl provided, cookie will be ignored.

# OneURL is found by accessing your Beyond-HD web site,
# hovering over the user icon and going to My Security then going to the One URL (OID) tab,
# and if it's not already active, you need to hit Reset One URL to activate it.
# Then use that link here.

class MainClass(Unit3D):
    URL = 'https://beyond-hd.me/'

    @classmethod
    def build_sign_in_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'oneurl': {'type': 'string'},
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def build_workflow(self, entry, config):
        site_config = entry['site_config']
        oneurl = site_config.get('oneurl')
        return [
            Work(
                url=oneurl or '/',
                method='get',
                succeed_regex='<title>BeyondHD | Beyond Your Imagination</title>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
                response_urls=['https://beyond-hd.me']
            )
        ]

    def build_selector(self):
        selector = {
            'user_id': '/([^.]+\.\d+)/badges"',
            'detail_sources': {
                'default': {
                    'link': '/{}',
                    'elements': {
                        'bar': '.table-responsive.well-style',
                        'date_table': '.bhd-profile'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': ('(上传|Upload).+?([\\d.]+ ?[ZEPTGMK]?iB)', 2)
                },
                'downloaded': {
                    'regex': ('(下载|Download).+?([\\d.]+ ?[ZEPTGMK]?iB)', 2)
                },
                'share_ratio': {
                    'regex': ('(分享率|Ratio).+?([\\d.]+)', 2)
                },
                'points': {
                    'regex': ('(魔力|BP:).+?(\\d[\\d,. ]*)', 2),
                    'handle': self.handle_points
                },
                'join_date': {
                    'regex': ('(注册日期|Member Since:) (\\d{4}-\\d{2}-\\d{2})', 2),
                    'handle': self.handle_join_date
                },
                'seeding': {
                    'regex': ('(\\d+)\\s*?(做种|Active Seeds)', 1)
                },
                'leeching': {
                    'regex': ('(\\d+)\\s*?(吸血|Active Downloads)', 1)
                },
                'hr': {
                    'regex': ('(警告|Warnings).+?(\\d+)', 2)
                }
            }
        }
        return selector

    def get_unit3d_message(self, entry, config, messages_url='/mail'):
        return super().get_unit3d_message(entry, config, messages_url)

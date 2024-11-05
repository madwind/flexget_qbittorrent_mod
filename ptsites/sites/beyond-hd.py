from typing import Final

from ..base.entry import SignInEntry
from ..base.sign_in import check_final_state, SignState, Work
from ..schema.unit3d import Unit3D
from ..utils.net_utils import get_module_name
from ..utils.value_handler import handle_join_date


# site_config
#    oneurl: 'xxxxxxxx'
#    cookie: 'xxxxxxxx'

# Choose between oneurl or cookie
# If oneurl provided, cookie will be ignored.

# OneURL is found by accessing your Beyond-HD website,
# hovering over the user icon and going to My Security then going to the One URL (OID) tab,
# and if it's not already active, you need to hit Reset One URL to activate it.
# Then use that link here.

class MainClass(Unit3D):
    URL: Final = 'https://beyond-hd.me/'

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'oneurl': {'type': 'string'},
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        site_config = entry['site_config']
        oneurl = site_config.get('oneurl')
        return [
            Work(
                url=oneurl or '/',
                method=self.sign_in_by_get,
                succeed_regex=['<title>BeyondHD | Beyond Your Imagination</title>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
                response_urls=['https://beyond-hd.me', 'https://beyond-hd.me/']
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': '/([^.]+\.\d+)/badges"',
            'detail_sources': {
                'default': {
                    'link': '/{}',
                    'elements': {
                        'bar': '.table-responsive.well-style',
                        'data_table': '.bhd-profile'
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
                    'handle': handle_join_date
                },
                'seeding': {
                    'regex': ('(\d+)\s*?\d*%\s*?(做种|Active Seeds)', 1)
                },
                'leeching': {
                    'regex': ('(\d+)\s*?(吸血|Active Downloads)', 1)
                },
                'hr': {
                    'regex': ('(警告|Warnings).+?(\\d+)', 2)
                }
            }
        }

import json
from io import BytesIO
from urllib.parse import urljoin

from ..base.base import SignState, NetworkState, Work
from ..schema.nexusphp import NexusPHP
from ..utils import baidu_ocr
from ..utils import net_utils
from ..utils.state_checkers import check_network_state

try:
    from PIL import Image
except ImportError:
    Image = None


class MainClass(NexusPHP):
    URL = 'https://hdsky.me/'
    TORRENT_PAGE_URL = '/details.php?id={torrent_id}&hit=1'
    DOWNLOAD_URL_REGEX = '/download\\.php\\?id=\\d+&passkey=.*?(?=")'
    USER_CLASSES = {
        'downloaded': [8796093022208, 10995116277760],
        'share_ratio': [5, 5.5],
        'days': [315, 455]
    }

    @classmethod
    def build_reseed_schema(cls):
        return {
            cls.get_module_name(): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'}
                },
                'additionalProperties': False
            }
        }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=['已签到'],
                check_state=('sign_in', SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/showup.php',
                method='ocr',
                succeed_regex=['{"success":true,"message":\\d+}'],
                fail_regex='{"success":false,"message":"invalid_imagehash"}',
                check_state=('final', SignState.SUCCEED),

                image_hash_url='/image_code_ajax.php',
                image_url='/image.php?action=regimage&imagehash={}',
            ),
        ]

    def sign_in_by_ocr(self, entry, config, work, last_content):
        data = {
            'action': (None, 'new')
        }
        image_hash_url = urljoin(entry['url'], work.image_hash_url)
        image_hash_response = self.request(entry, 'post', image_hash_url, files=data)
        image_hash_network_state = check_network_state(entry, image_hash_url, image_hash_response)
        if image_hash_network_state != NetworkState.SUCCEED:
            return
        content = net_utils.decode(image_hash_response)
        image_hash = json.loads(content)['code']

        if image_hash:
            image_url = urljoin(entry['url'], work.image_url)
            img_url = image_url.format(image_hash)
            img_response = self.request(entry, 'get', img_url)
            img_network_state = check_network_state(entry, img_url, img_response)
            if img_network_state != NetworkState.SUCCEED:
                return
        else:
            entry.fail_with_prefix('Cannot find: image_hash')
            return
        img = Image.open(BytesIO(img_response.content))
        code, img_byte_arr = baidu_ocr.get_ocr_code(img, entry, config)
        if code:
            if len(code) == 6:
                data = {
                    'action': (None, 'showup'),
                    'imagehash': (None, image_hash),
                    'imagestring': (None, code)
                }
                return self.request(entry, 'post', work.url, files=data)

    def build_selector(self):
        selector = super().build_selector()
        net_utils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector

    @classmethod
    def build_reseed_entry(cls, entry, config, site, passkey, torrent_id):
        cls.build_reseed_from_page(entry, config, passkey, torrent_id, cls.URL, cls.TORRENT_PAGE_URL,
                                   cls.DOWNLOAD_URL_REGEX)

import re
from io import BytesIO

from loguru import logger

try:
    from aip import AipOcr
except ImportError:
    AipOcr = None

try:
    from PIL import Image
except ImportError:
    Image = None


class BaiduOcr:
    @staticmethod
    def get_ocr_code(img, entry, config):
        app_id = config['aipocr'].get('app_id')
        api_key = config['aipocr'].get('api_key')
        secret_key = config['aipocr'].get('secret_key')

        if not (AipOcr and Image):
            entry.fail_with_prefix('Dependency does not exist: [baidu-aip, pillow]')
            return None, None
        if not (app_id and api_key and secret_key):
            entry.fail_with_prefix('AipOcr not set')
            return None, None

        client = AipOcr(app_id, api_key, secret_key)

        width = img.size[0]
        height = img.size[1]
        for i in range(0, width):
            for j in range(0, height):
                noise = BaiduOcr._detect_noise(img, i, j, width, height)
                if noise:
                    img.putpixel((i, j), (255, 255, 255))
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='png')
        response = client.basicAccurate(img_byte_arr.getvalue(), {"language_type": "ENG"})
        logger.info(response)
        if response.get('error_msg'):
            entry.fail_with_prefix(response.get('error_msg'))
            return None, None

        code = re.sub('\\W', '', response['words_result'][0]['words'])
        code = code.upper()
        return code, img_byte_arr

    @staticmethod
    def _detect_noise(img, i, j, width, height):
        if i < 25 or i > 122 or j < 15 or j > 24:
            return True
        pixel = img.getpixel((i, j))
        if pixel[0] != 0 or pixel[1] != 0 or pixel[2] != 0:
            return True
        else:
            if i + 1 < width:
                pixel = img.getpixel((i + 1, j))
                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    return False
            if i - 1 > 0:
                pixel = img.getpixel((i - 1, j))
                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    return False
            if j + 1 < height:
                pixel = img.getpixel((i, j + 1))
                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    return False
            if j - 1 > 0:
                pixel = img.getpixel((i, j + 1))
                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    return False
            return True

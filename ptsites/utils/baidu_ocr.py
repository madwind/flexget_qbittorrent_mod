from __future__ import annotations

import re
import threading
from io import BytesIO

from loguru import logger

from ..base.entry import SignInEntry

try:
    from aip import AipOcr
except ImportError:
    AipOcr = None

try:
    from PIL import Image
except ImportError:
    Image = None

qps = 1
lock = threading.Semaphore(qps)


def get_client(entry: SignInEntry, config: dict) -> AipOcr | None:
    if 'aipocr' not in config:
        entry.fail_with_prefix('aipocr not set in config')
        return None

    app_id = config['aipocr'].get('app_id')
    api_key = config['aipocr'].get('api_key')
    secret_key = config['aipocr'].get('secret_key')

    if not (AipOcr and Image):
        entry.fail_with_prefix('Dependency does not exist: [baidu-aip, pillow]')
        return None
    if not (app_id and api_key and secret_key):
        entry.fail_with_prefix('AipOcr not set')
        return None
    return AipOcr(app_id, api_key, secret_key)


def get_jap_ocr(img: Image.Image, entry: SignInEntry, config: dict) -> str | None:
    if not (client := get_client(entry, config)):
        return None
    img_byte_arr = BytesIO()

    if img.mode == "P":
        img = img.convert('RGB')

    img.save(img_byte_arr, format='JPEG')
    try:
        with lock:
            result = client.basicAccurate(img_byte_arr.getvalue(), {'language_type': 'JAP'})
    except Exception as e:
        entry.fail_with_prefix(f'baidu ocr error: {e}')
        return None
    logger.info(result)
    if result.get('error_msg'):
        entry.fail_with_prefix(result.get('error_msg'))
        return None
    text = ''
    for words_list in result.get('words_result'):
        text += words_list.get('words')
    return ''.join(re.findall(r'[\u2E80-\u9FFF]', text))


def get_ocr_code(img: Image.Image, entry: SignInEntry, config: dict) -> tuple:
    if not (client := get_client(entry, config)):
        return None, None

    # transform pixel value < black_threshold to pure black
    black_threshold = 64
    img = img.point(lambda p: 0 if p < black_threshold else p)

    width = img.size[0]
    height = img.size[1]
    for i in range(0, width):
        for j in range(0, height):
            if noise := _detect_noise(img, i, j, width, height):
                img.putpixel((i, j), (255, 255, 255))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='png')
    try:
        with lock:
            result = client.basicAccurate(img_byte_arr.getvalue(), {"language_type": "ENG"})
    except Exception as e:
        entry.fail_with_prefix('baidu ocr error.')
        return None, None
    logger.info(result)
    if result.get('error_msg'):
        entry.fail_with_prefix(result.get('error_msg'))
        return None, None

    code = re.sub('\\W', '', result['words_result'][0]['words'])
    code = code.upper()
    return code, img_byte_arr.getvalue()


def _detect_noise(img: Image.Image, i: int, j: int, width: int, height: int) -> bool:
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

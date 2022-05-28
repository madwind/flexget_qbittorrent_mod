import base64
import hashlib
import hmac
import struct
import sys
import time


def calc(secret_key: str) -> str:
    input_time = int(time.time()) // 30
    key = base64.b32decode(secret_key)
    msg = struct.pack(">Q", input_time)
    google_code = hmac.new(key, msg, hashlib.sha1).digest()
    o = google_code[19] & 15 if sys.version_info > (2, 7) else ord(str(google_code[19])) & 15
    google_code = str((struct.unpack(">I", google_code[o:o + 4])[0] & 0x7fffffff) % 1000000)
    return '0' + google_code if len(google_code) == 5 else google_code

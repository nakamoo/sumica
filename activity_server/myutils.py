import sys
import base64

import numpy as np

import settings

def base64_decode_image(a, size):
    if sys.version_info.major == 3:
        a = bytes(a, encoding="utf-8")

    a = np.frombuffer(base64.decodestring(a), dtype=np.uint8)
    a = a.reshape((size[1], size[0], settings.IMAGE_CHANS))

    return a
import base64
import zlib


def compress_data(data: str) -> str:
    return base64.b64encode(zlib.compress(data.encode(), level=9)).decode()


def decompress_data(compressed_data: str) -> str:
    return zlib.decompress(base64.b64decode(compressed_data)).decode()

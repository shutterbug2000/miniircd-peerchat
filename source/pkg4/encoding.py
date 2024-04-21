import base64
from typing import Union


def dwc_encode(buffer: Union[bytes, memoryview, bytearray]) -> str:
    return base64.standard_b64encode(buffer).decode().replace("=", "*")


def dwc_decode(buffer: str) -> bytes:
    return base64.standard_b64decode(
        buffer.replace("*", "=")
        .replace("?", "/")
        .replace(".", "+")
        .replace(">", "+")
        .replace("-", "/")
    )

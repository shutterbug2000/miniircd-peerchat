from datetime import datetime
from struct import pack, unpack
from typing import Union

# Nintendo Timestamps from services start from January 1st, 2000.
#
# Not the normal epoch of 1970.
__NINTENDO_EPOCH = datetime(2000, 1, 1)


def nintendo_epoch() -> int:
    return int((datetime.utcnow() - __NINTENDO_EPOCH).total_seconds())


def from_epoch(epoch: int) -> datetime:
    return datetime.fromtimestamp(epoch + __NINTENDO_EPOCH.timestamp())


class LobbyStartTime:
    def __init__(self, time: int):
        self.timestamp = time

    @staticmethod
    def from_serialized(
        buffer: Union[bytes, memoryview, bytearray]
    ) -> "LobbyStartTime":
        tuple = unpack("<Q", buffer)
        return LobbyStartTime(tuple[0])

    def to_serialized(self) -> bytes:
        return pack("<Q", self.timestamp)

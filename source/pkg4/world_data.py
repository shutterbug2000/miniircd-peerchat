from struct import pack, unpack
from typing import Union


class LobbyWorldData:
    """We don't validate the nation/area/flag as there's no use for them at the
    moment, and the game accepts any numbers just fine.
    """

    def __init__(self, nation: int, area: int, flag: int):
        self.nation = nation
        self.area = area
        self.flag = flag

    @staticmethod
    def from_serialized(
        buffer: Union[bytes, memoryview, bytearray]
    ) -> "LobbyWorldData":
        (raw_nation, raw_area, raw_flag) = unpack("<HBB", buffer)
        return LobbyWorldData(raw_nation, raw_area, raw_flag)

    def to_serialized(self) -> bytes:
        return pack("<HBB", self.nation, self.area, self.flag)

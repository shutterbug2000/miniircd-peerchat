from enum import Enum
from struct import pack, unpack
from typing import List, Union


class PlazaRoomType(Enum):
    FIRE = 0
    WATER = 1
    ELECTRIC = 2
    GRASS = 3
    MEW = 4


class PlazaRoomSeason(Enum):
    NONE = 0
    SPRING = 1
    SUMMER = 2
    FALL = 3
    WINTER = 4


class PlazaEvent(Enum):
    LOCK_ROOM = 0
    OVERHEAD_LIGHTING_BASE = 1
    OVERHEAD_ENDING_PHASE_ONE = 2
    OVERHEAD_ENDING_PHASE_TWO = 3
    OVERHEAD_ENDING_PHASE_THREE = 4
    OVERHEAD_ENDING_PHASE_FOUR = 5
    OVERHEAD_ENDING_PHASE_FIVE = 6
    STATUE_LIGHTING_BASE = 7
    STATUE_ENDING_PHASE_ONE = 8
    STATUE_ENDING_PHASE_TWO = 9
    STATUE_ENDING_PHASE_THREE = 10
    SPOTLIGHT_LIGHTING_BASE = 11
    SPOTLIGHT_ENDING_PHASE_ONE = 12
    SPOTLIGHT_ENDING_PHASE_TWO = 13
    SPOTLIGHT_ENDING_PHASE_THREE = 14
    END_ALL_MINIGAMES = 15
    START_FIREWORKS = 16
    END_FIREWORKS = 17
    CREATE_PARADE = 18
    CLOSE_PLAZA = 19


class PlazaEventTimestamp:
    def __init__(self, at_seconds: int, event: PlazaEvent):
        self.at_seconds = at_seconds
        self.event = event

    @staticmethod
    def from_serialized(
        buffer: Union[bytes, memoryview, bytearray]
    ) -> "PlazaEventTimestamp":
        (seconds, serialized_enum_ty) = unpack("<ii", buffer)
        return PlazaEventTimestamp(seconds, PlazaEvent(serialized_enum_ty))

    def to_serialized(self) -> bytes:
        return pack("<ii", self.at_seconds, self.event.value)


class PkWifiLobby:
    def __init__(
        self,
        lock_after_seconds: int,
        unk: int,
        bitflags: int,
        plaza_room_ty: PlazaRoomType,
        plaza_season: PlazaRoomSeason,
        events: List[PlazaEventTimestamp],
    ):
        self.lock_after = lock_after_seconds
        self.unk = unk
        self.arceus_bitflags = bitflags
        self.type = plaza_room_ty
        self.season = plaza_season
        self.events = events

    @staticmethod
    def from_serialized(buffer: Union[bytes, memoryview, bytearray]) -> "PkWifiLobby":
        buffer_view = memoryview(buffer)
        (
            raw_lock_after,
            raw_unk,
            raw_bitflags,
            raw_room_ty,
            raw_season,
            schedule_len,
        ) = unpack("<IIIBBH", buffer_view[:16])

        events = []
        memory_idx = 16
        for _ in range(0, schedule_len):
            events.append(
                PlazaEventTimestamp.from_serialized(
                    buffer_view[memory_idx : memory_idx + 8]
                )
            )
            memory_idx += 8
        if memory_idx != len(buffer_view):
            raise Exception(
                "PkWifiLobby had extra data at the end that wasn't understood"
                + f"{memory_idx} != {len(buffer_view)}"
            )

        return PkWifiLobby(
            raw_lock_after,
            raw_unk,
            raw_bitflags,
            PlazaRoomType(raw_room_ty),
            PlazaRoomSeason(raw_season),
            events,
        )

    def to_serialized(self) -> bytes:
        base_bytes = pack(
            "<IIIBBH",
            self.lock_after,
            self.unk,
            self.arceus_bitflags,
            self.type.value,
            self.season.value,
            len(self.events),
        )
        for event in self.events:
            base_bytes += event.to_serialized()
        return base_bytes

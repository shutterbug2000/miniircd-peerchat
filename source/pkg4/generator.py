from .lobby import (
    PlazaEventTimestamp,
    PlazaEvent,
    PlazaRoomSeason,
    PlazaRoomType,
    PkWifiLobby,
)
from datetime import datetime
import random
from typing import List

# A list of time tables to choose from.
#
# We've only gotten a confirmed capture from a 20 minute time schedule which was
# the lowest time ever reported. So we've created two other schedules at 25, and
# 30 minutes where we just offset the 20 minute schedule so it still hopefully
# feels real?
#
# Maybe someday we should just create our own time tables.
__TIME_TABLES: List[List[PlazaEventTimestamp]] = [
    # 20 Minute Schedule
    [
        PlazaEventTimestamp(0, PlazaEvent.OVERHEAD_LIGHTING_BASE),
        PlazaEventTimestamp(0, PlazaEvent.STATUE_LIGHTING_BASE),
        PlazaEventTimestamp(0, PlazaEvent.SPOTLIGHT_LIGHTING_BASE),
        PlazaEventTimestamp(780, PlazaEvent.STATUE_ENDING_PHASE_ONE),
        PlazaEventTimestamp(840, PlazaEvent.OVERHEAD_ENDING_PHASE_ONE),
        PlazaEventTimestamp(840, PlazaEvent.STATUE_ENDING_PHASE_TWO),
        PlazaEventTimestamp(900, PlazaEvent.OVERHEAD_ENDING_PHASE_TWO),
        PlazaEventTimestamp(900, PlazaEvent.OVERHEAD_ENDING_PHASE_THREE),
        PlazaEventTimestamp(900, PlazaEvent.SPOTLIGHT_ENDING_PHASE_ONE),
        PlazaEventTimestamp(960, PlazaEvent.OVERHEAD_ENDING_PHASE_THREE),
        PlazaEventTimestamp(960, PlazaEvent.STATUE_ENDING_PHASE_TWO),
        PlazaEventTimestamp(960, PlazaEvent.SPOTLIGHT_ENDING_PHASE_TWO),
        PlazaEventTimestamp(960, PlazaEvent.END_ALL_MINIGAMES),
        PlazaEventTimestamp(1020, PlazaEvent.OVERHEAD_ENDING_PHASE_FOUR),
        PlazaEventTimestamp(1020, PlazaEvent.SPOTLIGHT_ENDING_PHASE_THREE),
        PlazaEventTimestamp(1020, PlazaEvent.START_FIREWORKS),
        PlazaEventTimestamp(1075, PlazaEvent.CREATE_PARADE),
        PlazaEventTimestamp(1080, PlazaEvent.OVERHEAD_ENDING_PHASE_FIVE),
        PlazaEventTimestamp(1080, PlazaEvent.SPOTLIGHT_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1080, PlazaEvent.END_FIREWORKS),
        PlazaEventTimestamp(1140, PlazaEvent.SPOTLIGHT_LIGHTING_BASE),
        PlazaEventTimestamp(1200, PlazaEvent.CLOSE_PLAZA),
    ],
    # 25 Minute Schedule
    # - Same schedule as 20 minute, but just offset by 5 minutes.
    [
        PlazaEventTimestamp(0, PlazaEvent.OVERHEAD_LIGHTING_BASE),
        PlazaEventTimestamp(0, PlazaEvent.STATUE_LIGHTING_BASE),
        PlazaEventTimestamp(0, PlazaEvent.SPOTLIGHT_LIGHTING_BASE),
        PlazaEventTimestamp(1080, PlazaEvent.STATUE_ENDING_PHASE_ONE),
        PlazaEventTimestamp(1140, PlazaEvent.OVERHEAD_ENDING_PHASE_ONE),
        PlazaEventTimestamp(1140, PlazaEvent.STATUE_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1200, PlazaEvent.OVERHEAD_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1200, PlazaEvent.OVERHEAD_ENDING_PHASE_THREE),
        PlazaEventTimestamp(1200, PlazaEvent.SPOTLIGHT_ENDING_PHASE_ONE),
        PlazaEventTimestamp(1260, PlazaEvent.OVERHEAD_ENDING_PHASE_THREE),
        PlazaEventTimestamp(1260, PlazaEvent.STATUE_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1260, PlazaEvent.SPOTLIGHT_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1260, PlazaEvent.END_ALL_MINIGAMES),
        PlazaEventTimestamp(1320, PlazaEvent.OVERHEAD_ENDING_PHASE_FOUR),
        PlazaEventTimestamp(1320, PlazaEvent.SPOTLIGHT_ENDING_PHASE_THREE),
        PlazaEventTimestamp(1320, PlazaEvent.START_FIREWORKS),
        PlazaEventTimestamp(1375, PlazaEvent.CREATE_PARADE),
        PlazaEventTimestamp(1380, PlazaEvent.OVERHEAD_ENDING_PHASE_FIVE),
        PlazaEventTimestamp(1380, PlazaEvent.SPOTLIGHT_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1380, PlazaEvent.END_FIREWORKS),
        PlazaEventTimestamp(1440, PlazaEvent.SPOTLIGHT_LIGHTING_BASE),
        PlazaEventTimestamp(1500, PlazaEvent.CLOSE_PLAZA),
    ],
    # 30 Minute Schedule
    # - Same schedule as 20 minute, but offset by 10 minutes.
    [
        PlazaEventTimestamp(0, PlazaEvent.OVERHEAD_LIGHTING_BASE),
        PlazaEventTimestamp(0, PlazaEvent.STATUE_LIGHTING_BASE),
        PlazaEventTimestamp(0, PlazaEvent.SPOTLIGHT_LIGHTING_BASE),
        PlazaEventTimestamp(1380, PlazaEvent.STATUE_ENDING_PHASE_ONE),
        PlazaEventTimestamp(1440, PlazaEvent.OVERHEAD_ENDING_PHASE_ONE),
        PlazaEventTimestamp(1440, PlazaEvent.STATUE_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1500, PlazaEvent.OVERHEAD_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1500, PlazaEvent.OVERHEAD_ENDING_PHASE_THREE),
        PlazaEventTimestamp(1500, PlazaEvent.SPOTLIGHT_ENDING_PHASE_ONE),
        PlazaEventTimestamp(1560, PlazaEvent.OVERHEAD_ENDING_PHASE_THREE),
        PlazaEventTimestamp(1560, PlazaEvent.STATUE_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1560, PlazaEvent.SPOTLIGHT_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1560, PlazaEvent.END_ALL_MINIGAMES),
        PlazaEventTimestamp(1620, PlazaEvent.OVERHEAD_ENDING_PHASE_FOUR),
        PlazaEventTimestamp(1620, PlazaEvent.SPOTLIGHT_ENDING_PHASE_THREE),
        PlazaEventTimestamp(1620, PlazaEvent.START_FIREWORKS),
        PlazaEventTimestamp(1675, PlazaEvent.CREATE_PARADE),
        PlazaEventTimestamp(1680, PlazaEvent.OVERHEAD_ENDING_PHASE_FIVE),
        PlazaEventTimestamp(1680, PlazaEvent.SPOTLIGHT_ENDING_PHASE_TWO),
        PlazaEventTimestamp(1680, PlazaEvent.END_FIREWORKS),
        PlazaEventTimestamp(1740, PlazaEvent.SPOTLIGHT_LIGHTING_BASE),
        PlazaEventTimestamp(1800, PlazaEvent.CLOSE_PLAZA),
    ],
]


def __coin_flip() -> bool:
    return random.randint(1, 2) == 1


def generate_random_lobby() -> PkWifiLobby:
    room_ty = random.choices(
        [
            PlazaRoomType.FIRE,
            PlazaRoomType.WATER,
            PlazaRoomType.GRASS,
            PlazaRoomType.ELECTRIC,
            PlazaRoomType.MEW,
        ],
        # This gives fire/water/grass/electric as ~24.4% chance of being picked.
        # and gives mew a ~2.4% chance of being hit.
        [10, 10, 10, 10, 1],
    )[0]
    arceus_flag = 0x0
    if __coin_flip():
        arceus_flag = 0x1
    room_seasonality = PlazaRoomSeason.NONE
    # Should we give it any seasonality at all?
    if __coin_flip():
        # We give our current season a 62.5% chance of being selected,
        # then everything else a 12.5% chance.
        seasonality_chances = [10, 10, 10, 10]
        day = datetime.today().timetuple().tm_yday
        # "day of year" ranges for the northern hemisphere
        spring = range(80, 172)
        summer = range(172, 264)
        fall = range(264, 355)
        if day in spring:
            seasonality_chances[0] = 50
        elif day in summer:
            seasonality_chances[1] = 50
        elif day in fall:
            seasonality_chances[2] = 50
        else:
            seasonality_chances[3] = 50
        room_seasonality = random.choices(
            [
                PlazaRoomSeason.SPRING,
                PlazaRoomSeason.SUMMER,
                PlazaRoomSeason.FALL,
                PlazaRoomSeason.WINTER,
            ],
            seasonality_chances,
        )[0]
    schedule = random.choice(__TIME_TABLES)
    return PkWifiLobby(
        schedule[len(schedule) - 1].at_seconds,
        0,
        arceus_flag,
        room_ty,
        room_seasonality,
        schedule,
    )

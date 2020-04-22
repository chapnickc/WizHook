from dataclasses import dataclass
from typing import Dict, Any, Union, List, Tuple

RawSpotifyResponse = Dict[str, Any]

@dataclass
class EventSongChanged:
    analysis: RawSpotifyResponse
    start_time: float

@dataclass
class EventAdjustStartTime:
    start_time: float

@dataclass
class EventStop:
    ...

Event = Union[EventSongChanged, EventAdjustStartTime, EventStop]
Colors = List[Tuple[int, int, int]]

from dataclasses import dataclass
from typing import Any, Literal

type Songlist = dict[Any, Any]  # TODO implement

type SonglistCategory = Literal[
    "Nothing",
    "Concerts",
    "VocaloidRanking",
    "Pools",
    "Other",
]


@dataclass
class SonglistRelation:
    songlist_id: int
    name_hint: str

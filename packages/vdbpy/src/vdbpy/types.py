from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Entry_type = Literal[
    "Song",
    "Artist",
    "Album",
    "Tag",
    "ReleaseEvent",
    "SongList",
    "Venue",
    "ReleaseEventSeries",
]

Edit_type = Literal["Created", "Updated", "Deleted"]


@dataclass
class UserEdit:
    user_id: int
    edit_date: datetime
    entry_type: Entry_type
    entry_id: int
    version_id: int
    edit_event: Edit_type
    changed_fields: list[str]


# TODO type in form of 2024-01-01

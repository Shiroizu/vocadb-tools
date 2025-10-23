from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from vdbpy.types.changed_fields import ChangedFields

# TODO lint warning if type declaration missing
# TODO lint warning if not PascalCase

EntryType = Literal[
    "Song",
    "Artist",
    "Album",
    "Tag",
    "ReleaseEvent",
    "SongList",
    "Venue",
    "ReleaseEventSeries",
    "User",
]  # omit type here so this is possible:
# for entry_type in get_args(EntryType):

type SonglistCategory = Literal[
    "Nothing",
    "Concerts",
    "VocaloidRanking",
    "Pools",
    "Other",
]

type EntryId = int
type VersionId = int
type UserId = int
type Entry = tuple[EntryType, EntryId]

type EditType = Literal["Created", "Updated", "Deleted"]

type UserGroup = Literal[
    "Admin", "Moderator", "Trusted", "Regular", "Limited", "Nothing"
]
# Disabled User: active = false


@dataclass
class UserEdit:
    user_id: UserId
    edit_date: datetime
    entry_type: EntryType
    entry_id: EntryId
    version_id: VersionId
    edit_event: EditType
    changed_fields: list[ChangedFields]
    update_notes: str

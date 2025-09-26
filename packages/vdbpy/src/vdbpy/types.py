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

UserGroup = Literal["Admin", "Moderator", "Trusted", "Regular", "Limited", "Nothing"]
# Disabled User: active = false

TRUSTED_PLUS: list[UserGroup] = ["Admin", "Moderator", "Trusted"]
MOD_PLUS: list[UserGroup] = ["Admin", "Moderator"]

Songlist_category = Literal[
    "Nothing",
    "Concerts",
    "VocaloidRanking",
    "Pools",
    "Other",
]


@dataclass
class UserEdit:
    user_id: int
    edit_date: datetime
    entry_type: Entry_type
    entry_id: int
    version_id: int
    edit_event: Edit_type
    changed_fields: list[str]
    update_notes: str


Service = Literal[
    "NicoNicoDouga",
    "Youtube",
    "SoundCloud",
    "Vimeo",
    "Piapro",
    "BiliBili",
    "File",
    "LocalFile",
    "Creofuga",
    "Bandcamp",
]

RuleCheckResult = Literal[
    "Valid", "Rule violation", "Possible rule violation", "Not applicable"
]
VersionCheck = tuple[UserEdit, int, RuleCheckResult]
EntryCheck = list[list[VersionCheck]]

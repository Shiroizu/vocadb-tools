from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from vdbpy.types.artists import ArtistRole
    from vdbpy.types.songs import SongEntry

from vdbpy.types.changed_fields import ChangedFields
from vdbpy.types.users import UserId

type Comment = dict[Any, Any]  # TODO implement

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
]  # omit 'type' here so this is possible:
# for entry_type in get_args(EntryType):
# TODO investigate alternatives

# -------------------- types -------------------- #

type EntryId = int
type VersionId = int
type EntryTuple = tuple[EntryType, EntryId]
type EditType = Literal["Created", "Updated", "Deleted"]
type EntryStatus = Literal["Draft", "Finished", "Approved", "Locked"]

type ExternalLinkCategory = Literal["Official", "Commercial", "Reference", "Other"]
type PvType = Literal["Original", "Reprint", "Other"]
type Service = Literal[
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
type DefaultLanguage = Literal[
    "Unspecified", "Non-English", "Romaji", "English"
]  # "Japanese" --> "Non-English"
type NameMatchMode = Literal["Auto", "Partial", "StartsWith", "Exact", "Words"]

type Entry = (
    "SongEntry"
    # | AlbumEntry
    # | ArtistEntry
    # | TagEntry
    # | ReleaseEventEntry
    # | ReleaseEventSeriesEntry
    # | VenueEntry
    # | UserEntry
    # | SongListEntry
)

# -------------------- dataclasses -------------------- #


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


@dataclass
class Picture:
    picture_id: int
    mime: str
    name: str


@dataclass
class ExternalLink:
    category: ExternalLinkCategory
    description: str
    disabled: bool
    url: str
    # link_id: int


@dataclass
class VersionArtistParticipation:
    is_supporting: bool
    artist_id: int
    roles: list["ArtistRole"]
    name_hint: str


@dataclass
class PV:
    author: str
    disabled: bool
    length: int
    name: str
    pv_id: str
    pv_service: Service
    pv_type: PvType
    publish_date: datetime | None
    # skipped thumbUrl: str


@dataclass
class BaseEntryVersion:
    entry_id: int
    default_name_language: DefaultLanguage
    name_non_english: str
    name_romaji: str
    name_english: str
    aliases: list[str]
    description: str
    description_eng: str
    external_links: list[ExternalLink]
    status: EntryStatus  # from archivedVersion


@dataclass
class BaseEntry:
    id: int
    deleted: bool
    create_date: datetime
    default_name: str
    default_name_language: DefaultLanguage
    version_count: int
    status: EntryStatus

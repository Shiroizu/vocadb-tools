from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict

# --- Base --- #

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

Entry_status = Literal["Draft", "Finished", "Approved", "Locked"]

Default_languages = Literal["Unspecified", "Japanese", "Romaji", "English"]
External_link_category = Literal["Official, Commercial, Reference, Other"]

Artist_role = Literal[
    "Default",
    "Other",
    "Animator",
    "Arranger",
    "Composer",
    "Distributor",
    "Illustrator",
    "Instrumentalist",
    "Lyricist",
    "Mastering",
    "Publisher",
    "Vocalist",
    "VoiceManipulator",
    "Mixer",
    "VocalDataProvider",
]  # "Chorus", "Encoder",

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

PV_type = Literal["Original", "Reprint", "Other"]


@dataclass
class ExternalLink:
    category: External_link_category
    id: int
    url: str
    description: str
    description_url: str
    disabled: bool


class EntryNames(TypedDict):
    language: Default_languages
    value: str


@dataclass
class BaseEntryVersion:
    id: int
    default_name_language: Default_languages
    names: list[EntryNames]
    aliases: list[str]
    description: str
    description_eng: str
    external_links: list[ExternalLink]
    deleted: bool


@dataclass
class ArtistParticipation:
    is_supporting: bool
    artist_id: int
    roles: list[Artist_role]
    name_hint: str


@dataclass
class EventParticipation:
    event_id: int
    name_hint: str


@dataclass
class PV:
    author: str
    disabled: bool
    length: int
    name: str
    pv_id: str
    pv_service: Service
    pv_type: PV_type
    publish_date: datetime | None
    # thumbUrl: str


# --- Song --- #

Song_type = Literal[
    "Unspecified",
    "Original",
    "Remaster",
    "Remix",
    "Cover",
    "Arrangement",
    "Instrumental",
    "Mashup",
    "MusicPV",
    "DramaPV",
    "Other",
]  # Live, Rearrangement, ShortVersion, Illustration


@dataclass
class AlbumParticipation:
    disc_number: int
    track_number: int
    album_id: int
    name_hint: str


@dataclass
class Lyrics:
    language_codes: list[str]
    id: int
    source: str
    translation_type: Literal["Original", "Romanized", "Translation"]
    url: str
    value: str


@dataclass
class SongVersion(BaseEntryVersion):
    # Missing/unsupported fields:
    # - language_codes
    # - artist_string
    # - tags
    #
    # https://vocadb.net/api/songs/versions/x
    #  -> versions -> firstData

    albums: list[AlbumParticipation]
    artist: list[ArtistParticipation]
    length: int
    lyrics: list[Lyrics]
    min_milli_bpm = int
    max_milli_bpm = int
    original_version_id: int
    publish_date: datetime | None
    pvs: list[PV]
    release_events: list[EventParticipation]
    song_type: Song_type
    status: Entry_status  # from archivedVersion


# --- ArtistVersion --- #
# TODO

# --- AlbumVersion --- #
# TODO

# --- TagVersion --- #
# TODO

# --- ReleaseEventVersion --- #
# TODO

# --- VenueVersion --- #
# TODO

# --- ReleaseEventSeriesVersion --- #
# TODO


Songlist_category = Literal[
    "Nothing",
    "Concerts",
    "VocaloidRanking",
    "Pools",
    "Other",
]

# --- Entry --- #

EntryVersion = SongVersion  # | ArtistVersion | AlbumVersion | TagVersion | ReleaseEventVersion | VenueVersion | ReleaseEventSeriesVersion

# --- MikuMod --- #

Edit_type = Literal["Created", "Updated", "Deleted"]

UserGroup = Literal["Admin", "Moderator", "Trusted", "Regular", "Limited", "Nothing"]
# Disabled User: active = false

TRUSTED_PLUS: list[UserGroup] = ["Admin", "Moderator", "Trusted"]
MOD_PLUS: list[UserGroup] = ["Admin", "Moderator"]


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


RuleCheckResult = Literal[
    "Valid", "Rule violation", "Possible rule violation", "Not applicable", None
]
VersionCheck = tuple[UserEdit, int, RuleCheckResult]
EntryCheck = list[list[VersionCheck]]

Report_type = Literal[
    "InvalidInfo", "Duplicate", "Inappropriate", "Other", "InvalidTag", "BrokenPV"
]

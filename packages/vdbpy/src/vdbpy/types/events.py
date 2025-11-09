from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from vdbpy.types.series import EventSeriesRelation
from vdbpy.types.shared import BaseEntry, BaseEntryVersion
from vdbpy.types.songlists import SonglistRelation
from vdbpy.types.venues import VenueRelation

type ReleaseEventDetails = dict[Any, Any]  # TODO implement

# -------------------- types -------------------- #


type EventCategory = Literal[
    "Unspecified",
    "AlbumRelease",
    "Anniversary",
    "Club",
    "Concert",
    "Contest",
    "Convention",
    "Other",
    "Festival",
]

type EventArtistRole = Literal[
    "Default",
    "Dancer",
    "DJ",
    "Instrumentalist",
    "Organizer",
    "Promoter",
    "VJ",
    "Vocalist",
    "VoiceManipulator",
    "OtherPerformer",
    "Other",
]

# -------------------- dataclasses -------------------- #


@dataclass
class VersionEventArtistParticipation:
    artist_id: int
    roles: list[EventArtistRole]
    name_hint: str


@dataclass
class ReleaseEventVersion(BaseEntryVersion):
    # https://vocadb.net/api/tags/versions/x -> versions -> firstData
    # Missing/unsupported fields:
    # - endDate
    # - pvs
    autofilled_names: tuple[str, str, str] | None
    event_category: EventCategory
    start_date: datetime | None
    series_number: int
    series: EventSeriesRelation | None
    songlist: SonglistRelation | None
    venue: VenueRelation | None
    custom_venue_name: str
    artists: list[VersionEventArtistParticipation]


@dataclass
class ReleaseEvent:
    category: EventCategory
    date: datetime | None
    event_id: int
    name: str
    series_id: int
    series_number: int
    series_suffix: str
    status: str
    url_slug: str
    venue_name: str
    version_count: int

@dataclass
class OptionalReleaseEventFields:
    pass  # TODO implement

@dataclass
class ReleaseEventEntry(BaseEntry, OptionalReleaseEventFields):
    pass  # TODO implement

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from vdbpy.types.shared import (
        PV,
        EntryStatus,
        Picture,
        VersionArtistParticipation,
    )

from vdbpy.types.shared import BaseEntry, BaseEntryVersion

# -------------------- types -------------------- #


type AlbumType = Literal[
    "Unknown",
    "Album",
    "Single",
    "EP",
    "SplitAlbum",
    "Compilation",
    "Video",
    "Artbook",
    "Other",
    # Game, Fanmade, Instrumental, Drama
]

# -------------------- dataclasses -------------------- #


@dataclass
class Disc:
    disc_number: int
    disc_id: int
    media_type: Literal["Audio", "Video"]
    name: str


@dataclass
class AlbumTrack:
    disc_number: int
    track_number: int
    song_id: int
    name_hint: str


@dataclass
class AlbumVersion(BaseEntryVersion):
    # https://vocadb.net/api/albums/versions/x -> versions -> firstData
    # Missing/unsupported fields:
    # - mainPicture
    # Skipped fields:
    # - releaseEvent (legacy), e.g. https://vocadb.net/api/albums/versions/204261
    album_type: AlbumType
    artists: list["VersionArtistParticipation"]
    barcodes: list[str]
    catalog_number: str  # part of originalRelease
    discs: list[Disc]
    additional_pictures: list["Picture"]
    picture_mime: str
    publish_date: datetime | None  # part of originalRelease
    publish_day: int
    publish_month: int
    publish_year: int
    pvs: list["PV"]
    release_event_ids: list[int]  # part of originalRelease
    songs: list[AlbumTrack]


@dataclass
class Album:
    # api/songs?fields=Albums
    additional_names: str
    artist_string: str
    cover_picture_mime: str
    creation_date: datetime
    deleted: bool
    album_type: "AlbumType"
    album_id: int
    name: str
    rating_average: float
    rating_count: int
    release_year: int
    release_month: int
    release_day: int
    release_event_ids: list[int]
    version_count: int
    status: "EntryStatus"


@dataclass
class OptionalAlbumFields:
    pass  # TODO implement


@dataclass
class AlbumEntry(BaseEntry, OptionalAlbumFields):
    pass  # TODO implement

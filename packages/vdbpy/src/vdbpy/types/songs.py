from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

from vdbpy.types.albums import Album
from vdbpy.types.artists import ArtistParticipation, ArtistParticipationStatus
from vdbpy.types.events import ReleaseEvent
from vdbpy.types.shared import (
    PV,
    BaseEntry,
    BaseEntryVersion,
    DefaultLanguage,
    EntryStatus,
    ExternalLink,
    NameMatchMode,
    Service,
    VersionArtistParticipation,
)
from vdbpy.types.tags import Tag
from vdbpy.utils.data import to_camel_case
from vdbpy.utils.logger import get_logger

logger = get_logger()

# -------------------- types -------------------- #

type SongType = Literal[
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
]  # Skipped: Live, Rearrangement, ShortVersion, Illustration


type SongSortOption = Literal[
    "Name",
    "AdditionDate",
    "PublishDate",
    "FavoritedTimes",
    "RatingScore",
    "SongType",
]

type OptionalSongFieldNames = Literal[
    "albums",
    "artists",
    "lyrics",
    "names",
    "pvs",
    "releaseEvent",
    "tags",
    "webLinks",
    "bpm",
    "cultureCodes",
    # Skipped: "MainPicture", "ThumbUrl",
]


# -------------------- dataclasses -------------------- #


@dataclass
class Lyrics:
    language_codes: list[str]
    lyrics_id: int
    source: str
    translation_type: Literal["Original", "Romanized", "Translation"]
    url: str
    value: str


@dataclass
class SongVersion(BaseEntryVersion):
    # https://vocadb.net/api/songs/versions/x -> versions -> firstData
    # Missing/unsupported fields:
    # - language_codes
    artists: list[VersionArtistParticipation]
    length_seconds: int
    lyrics: list[Lyrics]
    max_milli_bpm: int
    min_milli_bpm: int
    original_version_id: int
    publish_date: datetime | None
    pvs: list[PV]
    release_event_ids: list[int]
    song_type: SongType


@dataclass
class OptionalSongFields:
    albums: list[Album] | Literal["Unknown"]
    artists: list[ArtistParticipation] | Literal["Unknown"]
    lyrics: list[Lyrics] | Literal["Unknown"]
    names: dict[DefaultLanguage, str] | Literal["Unknown"]
    aliases: list[str] | Literal["Unknown"]
    pvs: list[PV] | Literal["Unknown"]
    release_events: list[ReleaseEvent] | Literal["Unknown"]
    tags: list[Tag] | Literal["Unknown"]
    external_links: list[ExternalLink] | Literal["Unknown"]
    max_milli_bpm: int | None | Literal["Unknown"]
    min_milli_bpm: int | None | Literal["Unknown"]
    languages: list[str] | Literal["Unknown"]


@dataclass
class SongEntry(BaseEntry, OptionalSongFields):
    artist_string: str
    favorite_count: int
    length_seconds: int
    original_version_id: int
    publish_date: datetime | None
    pv_services: list[Service]
    rating_score: int
    song_type: SongType


@dataclass
class SongSearchParams:
    # ! = renamed url param
    max_results: int = 0
    start: int = 0
    query: str = ""
    sort: SongSortOption | None = None
    name_match_mode: NameMatchMode = "Auto"
    status: EntryStatus | None = None
    song_types: set[SongType] | None = None
    published_after_date: datetime | None = None  # ! afterDate
    published_before_date: datetime | None = None  # ! beforeDate
    hours_more_recent_than: int = 0  # ! since
    tag_ids: set[int] | None = None  # ! tagId[]
    tag_names: set[str] | None = None  # ! tagName[]
    excluded_tag_ids: set[int] | None = None  # ! excludedTagIds[]
    include_child_tags: bool = False  # ! childTags
    unify_types_and_tags: bool = False
    artist_ids: set[int] | None = None  # ! artistId[]
    artist_participation_status: ArtistParticipationStatus | None = None
    include_child_voicebanks: bool = False  # ! childVoicebanks
    include_group_members: bool = False  # ! includeMembers
    only_with_pvs: bool = False
    pv_service: Service | None = None  # ! pvServices
    min_score: int = 0
    user_collection_id: int = 0
    release_event_id: int = 0
    original_version_id: int = 0  # ! parentSongId
    min_milli_bpm: int = 0
    max_milli_bpm: int = 0
    min_length: int = 0
    max_length: int = 0
    languages: set[str] | None = None  # ! language --> languages[]

    def to_url_params(self) -> dict[str, str | int | list[str]]:
        rename_mapping = {
            "hours_more_recent_than": "since",
            "excluded_tag_ids": "excludedTagIds[]",
            "include_child_tags": "childTags",
            "artist_ids": "artistId[]",
            "include_child_voicebanks": "childVoicebanks",
            "include_group_members": "includeMembers",
            "pv_service": "pvServices",
            "tag_ids": "tagId[]",
            "tag_names": "tagName[]",
            "original_version_id": "parentSongId",
            "published_after_date": "afterDate",
            "published_before_date": "beforeDate",
            "languages": "languages[]",
        }

        params: dict[str, str | int | list[str]] = {}

        for field_name, value in asdict(self).items():
            if not value:
                continue

            renamed_field_name = rename_mapping.get(
                field_name, to_camel_case(field_name)
            )

            if isinstance(value, set):
                logger.info(f"Parsing set field values {value}")
                value_str_list: list[str] = list(map(str, value))  # type: ignore
                logger.info(f"Set string {value_str_list}")
                if renamed_field_name.endswith("[]"):
                    if len(value_str_list) == 1:
                        params[renamed_field_name] = value_str_list[0]
                        continue
                    params[renamed_field_name] = value_str_list
                    continue
                params[renamed_field_name] = ",".join(value_str_list)

            elif isinstance(value, datetime):
                params[renamed_field_name] = str(value.isoformat())

            else:
                params[renamed_field_name] = value

        return params

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# ------------ Shared types ------------ #

type EntryStatus = Literal["Draft", "Finished", "Approved", "Locked"]

type DefaultLanguages = Literal[
    "Unspecified", "Non-English", "Romaji", "English"
]  # JP = "Non-English"
type ExternalLinkCategory = Literal["Official", "Commercial", "Reference", "Other"]


type ArtistRole = Literal[
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

type PvType = Literal["Original", "Reprint", "Other"]


@dataclass
class ExternalLink:
    category: ExternalLinkCategory
    description: str
    disabled: bool
    url: str


@dataclass
class ArtistParticipation:
    is_supporting: bool
    artist_id: int
    roles: list[ArtistRole]
    name_hint: str


@dataclass
class EventArtistParticipation:
    artist_id: int
    roles: list[EventArtistRole]
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
    pv_type: PvType
    publish_date: datetime | None
    # thumbUrl: str


@dataclass
class BaseEntryVersion:
    entry_id: int
    default_name_language: DefaultLanguages
    name_non_english: str
    name_romaji: str
    name_english: str
    aliases: list[str]
    description: str
    description_eng: str
    external_links: list[ExternalLink]
    status: EntryStatus  # from archivedVersion


# ------------ SongVersion ------------ #

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
    artists: list[ArtistParticipation]
    length: int
    lyrics: list[Lyrics]
    max_milli_bpm = int
    min_milli_bpm = int
    original_version_id: int
    publish_date: datetime | None
    pvs: list[PV]
    release_events: list[EventParticipation]
    song_type: SongType


# ------------ AlbumVersion ------------ #

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


@dataclass
class Disc:
    disc_number: int
    disc_id: int
    media_type: Literal["Audio", "Video"]
    name: str


@dataclass
class Picture:
    picture_id: int
    mime: str
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
    # - mainPictureMime
    # - releaseEvent (legacy), e.g. https://vocadb.net/api/albums/versions/204261
    album_type: AlbumType
    artists: list[ArtistParticipation]
    barcodes: list[str]
    catalog_number: str  # part of originalRelease
    discs: list[Disc]
    additional_pictures: list[Picture]
    publish_date: datetime | None  # part of originalRelease
    publish_day: int
    publish_month: int
    publish_year: int
    pvs: list[PV]
    release_events: list[EventParticipation]  # part of originalRelease
    songs: list[AlbumTrack]


# --- ArtistVersion --- #

VoicebankType = Literal[
    "Vocaloid",
    "UTAU",
    "CeVIO",
    "OtherVoiceSynthesizer",
    "SynthesizerV",
    "NEUTRINO",
    "VoiSona",
    "NewType",
    "Voiceroid",
    "VOICEVOX",
    "ACEVirtualSinger",
    "AIVOICE",
]

BasicArtistType = Literal[
    "Unknown",
    "Circle",
    "Label",
    "OtherGroup",
    "Producer",
    "Animator",
    "Illustrator",
    "Lyricist",
    "OtherVocalist",
    "OtherIndividual",
    "CoverArtist",
    "Instrumentalist",
]
# "Utaite", "Band", "Vocalist", "Character", "Designer"

type ArtistType = VoicebankType | BasicArtistType


@dataclass
class ArtistVersion(BaseEntryVersion):
    # https://vocadb.net/api/artists/versions/x -> versions -> firstData
    # Skipped fields:
    # - mainPictureMime
    # - members
    artist_type: ArtistType
    group_ids: list[int]
    vb_voice_provider_ids: list[int]
    vb_manager_ids: list[int]
    vb_illustrator_ids: list[int]
    vb_chara_designer_ids: list[int]
    vb_base_id: int
    vb_release_date: datetime | None
    additional_pictures: list[Picture]


# --- TagVersion --- #

type TagCategory = Literal[
    "Genres",
    "Animation",
    "Composition",
    "Copyrights",
    "Derivative",
    "Distribution",
    "Event",
    "Games",
    "Instruments",
    "Jobs",
    "Languages",
    "Lyrics",
    "Media",
    "MMD Models",
    "Series",
    "Sources",
    "Subjective",
    "Themes",
    "Vocalists",
]


@dataclass
class TagRelation:
    tag_id: int
    name_hint: str


@dataclass
class TagVersion(BaseEntryVersion):
    # https://vocadb.net/api/tags/versions/x -> versions -> firstData
    # Missing/unsupported fields:
    # - targets (new & old)
    tag_category: TagCategory | str
    hidden_from_suggestions: bool
    parent_tag: TagRelation | None
    related_tags: list[TagRelation]


# --- ReleaseEventVersion --- #

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


@dataclass
class EventSeriesRelation:
    series_id: int
    name_hint: str


@dataclass
class SonglistRelation:
    songlist_id: int
    name_hint: str


@dataclass
class VenueRelation:
    venue_id: int
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
    artists: list[EventArtistParticipation]


# --- ReleaseEventSeriesVersion --- #
@dataclass
class ReleaseEventSeriesVersion(BaseEntryVersion):
    autofilled_names: tuple[str, str, str] | None
    event_category: EventCategory


# --- VenueVersion --- #
@dataclass
class VenueVersion(BaseEntryVersion):
    autofilled_names: tuple[str, str, str] | None
    address: str | None
    country_code: str | None
    latitude: float | None
    longitude: float | None


# --- EntryVersion --- #

type EntryVersion = (
    SongVersion
    | ArtistVersion
    | AlbumVersion
    | TagVersion
    | ReleaseEventVersion
    | ReleaseEventSeriesVersion
    | VenueVersion
)

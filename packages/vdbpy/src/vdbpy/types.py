from dataclasses import dataclass
from datetime import datetime
from types import ModuleType
from typing import Literal

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
    "User"
]

Entry = tuple[Entry_type, int]  # entry_id

entry_type_to_url: dict[Entry_type, str] = {
    "Song": "S",
    "Artist": "Ar",
    "Album": "Al",
    "Venue": "Venue/Details",
    "Tag": "T",
    "ReleaseEvent": "E",
    "ReleaseEventSeries": "Es",
    "SongList": "L",
}

entry_url_to_type: dict[str, Entry_type] = {v: k for k, v in entry_type_to_url.items()}

Entry_status = Literal["Draft", "Finished", "Approved", "Locked"]

Default_languages = Literal[
    "Unspecified", "Non-English", "Romaji", "English"
]  # JP = "Non-English"
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

Event_artist_role = Literal[
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
    description: str
    disabled: bool
    url: str


@dataclass
class ArtistParticipation:
    is_supporting: bool
    artist_id: int
    roles: list[Artist_role]
    name_hint: str


@dataclass
class EventArtistParticipation:
    artist_id: int
    roles: list[Event_artist_role]
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


@dataclass
class BaseEntryVersion:
    entry_id: int
    default_name_language: Default_languages
    name_non_english: str
    name_romaji: str
    name_english: str
    aliases: list[str]
    description: str
    description_eng: str
    external_links: list[ExternalLink]
    status: Entry_status  # from archivedVersion


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
    albums: list[AlbumParticipation]
    artists: list[ArtistParticipation]
    length: int
    lyrics: list[Lyrics]
    max_milli_bpm = int
    min_milli_bpm = int
    original_version_id: int
    publish_date: datetime | None
    pvs: list[PV]
    release_events: list[EventParticipation]
    song_type: Song_type


# --- AlbumVersion --- #

Album_type = Literal[
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
    album_type: Album_type
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

Voicebank_type = Literal[
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

Basic_artist_type = Literal[
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

Artist_type = Voicebank_type | Basic_artist_type


@dataclass
class ArtistVersion(BaseEntryVersion):
    # https://vocadb.net/api/artists/versions/x -> versions -> firstData
    # Skipped fields:
    # - mainPictureMime
    # - members
    artist_type: Artist_type
    group_ids: list[int]
    vb_voice_provider_ids: list[int]
    vb_manager_ids: list[int]
    vb_illustrator_ids: list[int]
    vb_chara_designer_ids: list[int]
    vb_base_id: int
    vb_release_date: datetime | None
    additional_pictures: list[Picture]


# --- TagVersion --- #

Tag_category = Literal[
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
    tag_category: Tag_category | str
    hidden_from_suggestions: bool
    parent_tag: TagRelation | None
    related_tags: list[TagRelation]


# --- ReleaseEventVersion --- #

Event_category = Literal[
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
    event_category: Event_category
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
    event_category: Event_category


# --- VenueVersion --- #
@dataclass
class VenueVersion(BaseEntryVersion):
    autofilled_names: tuple[str, str, str] | None
    address: str | None
    country_code: str | None
    latitude: float | None
    longitude: float | None


# --------------------------------- #

Songlist_category = Literal[
    "Nothing",
    "Concerts",
    "VocaloidRanking",
    "Pools",
    "Other",
]

# --- Entry --- #

EntryVersion = (
    SongVersion
    | ArtistVersion
    | AlbumVersion
    | TagVersion
    | ReleaseEventVersion
    | ReleaseEventSeriesVersion
    | VenueVersion
)

# --- MikuMod --- #

Edit_type = Literal["Created", "Updated", "Deleted"]

UserGroup = Literal["Admin", "Moderator", "Trusted", "Regular", "Limited", "Nothing"]
# Disabled User: active = false

TRUSTED_PLUS: list[UserGroup] = ["Admin", "Moderator", "Trusted"]
MOD_PLUS: list[UserGroup] = ["Admin", "Moderator"]

# From github/vocadb/VocaDbModel/Domain/{entry_type}s/{entry_type}Diff.cs
Changed_song_fields = Literal[
    "Artists",
    "Length",
    "Lyrics",
    "Names",
    "Notes",
    "OriginalName",
    "OriginalVersion",
    "PublishDate",
    "PVs",
    "ReleaseEvent",
    "ReleaseEvents",
    "SongType",
    "Status",
    "WebLinks",
    "Bpm",
    "CultureCodes",
]
Changed_album_fields = Literal[
    "Artists",
    "Cover",
    "Description",
    "Discs",
    "DiscType",
    "Identifiers",
    "Names",
    "OriginalName",
    "OriginalRelease",
    "Pictures",
    "PVs",
    "Status",
    "Tracks",
    "WebLinks",
]
Changed_artist_fields = Literal[
    "Albums",
    "ArtistType",
    "BaseVoicebank",
    "Description",
    "Groups",
    "Names",
    "OriginalName",
    "Picture",
    "Pictures",
    "ReleaseDate",
    "Status",
    "WebLinks",
    "CultureCodes",
]
Changed_tag_fields = Literal[
    "CategoryName",
    "Description",
    "HideFromSuggestions",
    "Names",
    "OriginalName",
    "Parent",
    "Picture",
    "RelatedTags",
    "Status",
    "Targets",
    "WebLinks",
]
Changed_venue_fields = Literal[
    "Address",
    "AddressCountryCode",
    "Coordinates",
    "Description",
    "OriginalName",
    "Names",
    "Status",
    "WebLinks",
]
Changed_release_event_fields = Literal[
    "Artists",
    "Category",
    "Date",
    "Description",
    "MainPicture",
    "Names",
    "OriginalName",
    "PVs",
    "Series",
    "SeriesNumber",
    "SeriesSuffix",
    "SongList",
    "Status",
    "Venue",
    "VenueName",
    "WebLinks",
]
Changed_release_event_series_fields = Literal[
    "Category", "Description", "OriginalName", "Names", "Picture", "Status", "WebLinks"
]

Changed_fields = (
    Changed_song_fields
    | Changed_album_fields
    | Changed_artist_fields
    | Changed_tag_fields
    | Changed_venue_fields
    | Changed_release_event_fields
    | Changed_release_event_series_fields
)


@dataclass
class UserEdit:
    user_id: int
    edit_date: datetime
    entry_type: Entry_type
    entry_id: int
    version_id: int
    edit_event: Edit_type
    changed_fields: list[Changed_fields]
    update_notes: str


RuleCheckResult = Literal[
    "Valid",
    "Rule violation",
    "Possible rule violation",
    "Not applicable",
    "Unrelated fields",
    None,
]
VersionCheck = tuple[UserEdit, int, RuleCheckResult]
EntryCheck = list[list[VersionCheck]]


Report_type = Literal[
    "InvalidInfo", "Duplicate", "Inappropriate", "Other", "InvalidTag", "BrokenPV"
]


@dataclass
class EntryReport:
    report_id: int
    entry_type: Entry_type
    entry_id: int
    date: datetime
    report_type: Report_type
    notes: str
    author: int | Literal["anon"]


RuleModules = dict[int, tuple[str, ModuleType]]
# rule_id: (rule_name, rule_module)

EntryReportWithVersion = tuple[EntryReport, int]
ParsedEntryReport = list[EntryReportWithVersion | Entry]
ParsedReportsByRuleId = dict[int, ParsedEntryReport]
ParsedReportsByRuleIdByUserId = dict[int, ParsedReportsByRuleId]

Report_result = Literal[
    "Success", "Too old", "Too recent", "Skipped", "Error", "Deleted"
]

Test_version = tuple[RuleCheckResult, list[tuple[Entry_type, int]]]

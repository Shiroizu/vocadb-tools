from dataclasses import dataclass
from datetime import datetime
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
]

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
    artist: list[ArtistParticipation]
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
    # Missing/unsupported fields:
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
@dataclass
class TagVersion(BaseEntryVersion):
    pass


# --- ReleaseEventVersion --- #
@dataclass
class ReleaseEventVersion(BaseEntryVersion):
    pass


# --- VenueVersion --- #
@dataclass
class VenueVersion(BaseEntryVersion):
    pass


# --- ReleaseEventSeriesVersion --- #
@dataclass
class ReleaseEventSeriesVersion(BaseEntryVersion):
    pass


# --------------------------------- #

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
    "Valid", "Rule violation", "Possible rule violation", "Not applicable", None
]
VersionCheck = tuple[UserEdit, int, RuleCheckResult]
EntryCheck = list[list[VersionCheck]]

Report_type = Literal[
    "InvalidInfo", "Duplicate", "Inappropriate", "Other", "InvalidTag", "BrokenPV"
]

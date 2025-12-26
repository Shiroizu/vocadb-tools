from typing import Literal

# From github/vocadb/VocaDbModel/Domain/{entry_type}s/{entry_type}Diff.cs
type ChangedSongFields = Literal[
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

# from vdbpy.types.songs import SongVersion
# Unsupported: "CultureCodes",
song_version_fields_to_changed_song_fields_mapping: dict[str, ChangedSongFields] = {
    "artists": "Artists",
    "lyrics": "Lyrics",
    "publish_date": "PublishDate",
    "pvs": "PVs",
    "song_type": "SongType",
    "status": "Status",
    # ------
    "name_non_english": "Names",
    "name_romaji": "Names",
    "name_english": "Names",
    "aliases": "Names",
    "description": "Notes",
    "description_eng": "Notes",
    "length_seconds": "Length",
    "default_name_language": "OriginalName",
    "original_version_id": "OriginalVersion",
    "release_event_ids": "ReleaseEvents",
    "external_links": "WebLinks",
    "max_milli_bpm": "Bpm",
    "min_milli_bpm": "Bpm",
}

type ChangedAlbumFields = Literal[
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

type ChangedArtistFields = Literal[
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

type ChangedTagFields = Literal[
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

type ChangedVenueFields = Literal[
    "Address",
    "AddressCountryCode",
    "Coordinates",
    "Description",
    "OriginalName",
    "Names",
    "Status",
    "WebLinks",
]

type ChangedReleaseEventFields = Literal[
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

type ChangedReleaseEventSeriesFields = Literal[
    "Category", "Description", "OriginalName", "Names", "Picture", "Status", "WebLinks"
]

type ChangedFields = (
    ChangedSongFields
    | ChangedAlbumFields
    | ChangedArtistFields
    | ChangedTagFields
    | ChangedVenueFields
    | ChangedReleaseEventFields
    | ChangedReleaseEventSeriesFields
)

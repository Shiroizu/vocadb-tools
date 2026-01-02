from typing import Literal

type SharedChangedFields = Literal[
    "Status",
    "OriginalName",
    "Names",
    "WebLinks"
]

# From github/vocadb/VocaDbModel/Domain/{entry_type}s/{entry_type}Diff.cs
type ChangedSongFields = Literal[
    SharedChangedFields,
    "Artists",
    "Length",
    "Lyrics",
    "Notes",
    "OriginalVersion",
    "PublishDate",
    "PVs",
    "ReleaseEvent",
    "ReleaseEvents",
    "SongType",
    "Bpm",
    "CultureCodes",
]

type ChangedAlbumFields = Literal[
    SharedChangedFields,
    "Artists",
    "Cover",
    "Description",
    "Discs",
    "DiscType",
    "Identifiers",
    "OriginalRelease",
    "Pictures",
    "PVs",
    "Tracks",
]

type ChangedArtistFields = Literal[
    SharedChangedFields,
    "Albums",
    "ArtistType",
    "BaseVoicebank",
    "Description",
    "Groups",
    "Picture",
    "Pictures",
    "ReleaseDate",
    "CultureCodes",
]

type ChangedTagFields = Literal[
    SharedChangedFields,
    "CategoryName",
    "Description",
    "HideFromSuggestions",
    "Parent",
    "Picture",
    "RelatedTags",
    "Targets",
]

type ChangedVenueFields = Literal[
    SharedChangedFields,
    "Address",
    "AddressCountryCode",
    "Coordinates",
    "Description",
]

type ChangedReleaseEventFields = Literal[
    SharedChangedFields,
    "Artists",
    "Category",
    "Date",
    "Description",
    "MainPicture",
    "PVs",
    "Series",
    "SeriesNumber",
    "SeriesSuffix",
    "SongList",
    "Venue",
    "VenueName",
]

type ChangedReleaseEventSeriesFields = Literal[
    SharedChangedFields,
    "Category", "Description", "OriginalName", "Picture", "WebLinks"
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

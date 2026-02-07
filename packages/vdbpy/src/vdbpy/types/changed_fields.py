from typing import Literal, TypeAlias

SharedChangedFields: TypeAlias = Literal["Status", "OriginalName", "Names", "WebLinks"]

# From github/vocadb/VocaDbModel/Domain/{entry_type}s/{entry_type}Diff.cs
ChangedSongFields: TypeAlias = Literal[
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

ChangedAlbumFields: TypeAlias = Literal[
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

ChangedArtistFields: TypeAlias = Literal[
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

ChangedTagFields: TypeAlias = Literal[
    SharedChangedFields,
    "CategoryName",
    "Description",
    "HideFromSuggestions",
    "Parent",
    "Picture",
    "RelatedTags",
    "Targets",
]

ChangedVenueFields: TypeAlias = Literal[
    SharedChangedFields,
    "Address",
    "AddressCountryCode",
    "Coordinates",
    "Description",
]

ChangedReleaseEventFields: TypeAlias = Literal[
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

ChangedReleaseEventSeriesFields: TypeAlias = Literal[
    SharedChangedFields,
    "Category",
    "Description",
    "OriginalName",
    "Picture",
    "WebLinks",
]

ChangedFields: TypeAlias = (
    ChangedSongFields
    | ChangedAlbumFields
    | ChangedArtistFields
    | ChangedTagFields
    | ChangedVenueFields
    | ChangedReleaseEventFields
    | ChangedReleaseEventSeriesFields
)

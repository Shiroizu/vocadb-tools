from typing import Literal

SharedChangedFields = Literal["Status", "OriginalName", "Names", "WebLinks"]

# From github/vocadb/VocaDbModel/Domain/{entry_type}s/{entry_type}Diff.cs
ChangedSongFields = Literal[
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

ChangedAlbumFields = Literal[
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

ChangedArtistFields = Literal[
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

ChangedTagFields = Literal[
    SharedChangedFields,
    "CategoryName",
    "Description",
    "HideFromSuggestions",
    "Parent",
    "Picture",
    "RelatedTags",
    "Targets",
]

ChangedVenueFields = Literal[
    SharedChangedFields,
    "Address",
    "AddressCountryCode",
    "Coordinates",
    "Description",
]

ChangedReleaseEventFields = Literal[
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

ChangedReleaseEventSeriesFields = Literal[
    SharedChangedFields,
    "Category",
    "Description",
    "OriginalName",
    "Picture",
    "WebLinks",
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

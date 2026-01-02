from typing import Literal

from vdbpy.config import (
    ALBUM_API_URL,
    ARTIST_API_URL,
    EVENT_API_URL,
    SERIES_API_URL,
    SONG_API_URL,
    TAG_API_URL,
    VENUE_API_URL,
)
from vdbpy.types.changed_fields import (
    ChangedAlbumFields,
    ChangedArtistFields,
    ChangedFields,
    ChangedReleaseEventFields,
    ChangedReleaseEventSeriesFields,
    ChangedSongFields,
    ChangedTagFields,
    ChangedVenueFields,
    SharedChangedFields,
)
from vdbpy.types.shared import EditType, EntryType

edit_event_map: dict[str, EditType] = {
    "Created": "Created",
    "Updated": "Updated",
    "PropertiesUpdated": "Updated",
    "Reverted": "Reverted",
    "Deleted": "Deleted",
    "Merged": "Updated",
    "Restored": "Restored",
}
entry_type_to_url: dict[EntryType, str] = {
    "Song": "S",
    "Artist": "Ar",
    "Album": "Al",
    "Venue": "Venue/Details",
    "Tag": "T",
    "ReleaseEvent": "E",
    "ReleaseEventSeries": "Es",
    "SongList": "L",
}
entry_url_to_type: dict[str, EntryType] = {v: k for k, v in entry_type_to_url.items()}
api_urls_by_entry_type: dict[EntryType, str] = {
    "Song": SONG_API_URL,
    "Album": ALBUM_API_URL,
    "Artist": ARTIST_API_URL,
    "Tag": TAG_API_URL,
    "ReleaseEvent": EVENT_API_URL,
    "ReleaseEventSeries": SERIES_API_URL,
    "Venue": VENUE_API_URL,
}
entry_types_by_api_url: dict[str, EntryType] = {
    v: k for k, v in api_urls_by_entry_type.items()
}

# from vdbpy.types.songs import SongVersion
# Unsupported: "CultureCodes",
renamed_version_fields_to_changed_fields_mapping_by_entry_type: dict[
    str, dict[EntryType | Literal["Shared"], ChangedFields]
] = {
    "Shared": {
        "name_non_english": "Names",
        "name_romaji": "Names",
        "name_english": "Names",
        "aliases": "Names",
        "default_name_language": "OriginalName",
        "external_links": "WebLinks",
        "description_eng": "Description",
    },
    "Song": {
        "description": "Notes",
        "description_eng": "Notes",
        "length_seconds": "Length",
        "original_version_id": "OriginalVersion",
        "release_event_ids": "ReleaseEvents",
        "max_milli_bpm": "Bpm",
        "min_milli_bpm": "Bpm",
    },
    "Artist": {
        "vb_base_id": "BaseVoicebank",
        "additional_pictures": "Pictures",
        "vb_voice_provider_ids": "Groups",
        "vb_manager_ids": "Groups",
        "vb_illustrator_ids": "Groups",
        "vb_chara_designer_ids": "Groups",
        "vb_release_date": "ReleaseDate",
    },
    "Album": {
        "album_type": "DiscType",
        "picture_mime": "Cover",
        "additional_pictures": "Pictures",
        "pvs": "PVs",
        "songs": "Tracks",
        "barcodes": "Identifiers",
        "catalog_number": "originalRelease",
        "publish_date": "originalRelease",
        "publish_day": "originalRelease",
        "publish_month": "originalRelease",
        "publish_year": "originalRelease",
        "release_event_ids": "originalRelease",
    },
    "Tag": {
        "tag_category": "CategoryName",
        "hidden_from_suggestions": "HideFromSuggestions",
        "parent_tag": "Parent",
        "related_tags": "RelatedTags",
    },
    "ReleaseEvent": {
        "event_category": "Category",
        "start_date": "Date",
        "custom_venue_name": "VenueName",
        "songlist": "SongList",
    },
    "ReleaseEventSeries": {},
    "Venue": {
        "country_code": "AddressCountryCode",
        "latitude": "Coordinates",
        "longitude": "Coordinates",
    },
}  # type: ignore

derived_fields_by_entry_type: dict[EntryType, list[ChangedFields]] = {
    "Song": ["Lyrics"],
    "Artist": ["Groups"],  # Voicebanks only
    "ReleaseEvent": ["Category", "Names", "OriginalName"],
}

changed_fields_by_entry_type: dict[EntryType | Literal["Shared"], ChangedFields] = {
    "Song": ChangedSongFields,
    "Album": ChangedAlbumFields,
    "Artist": ChangedArtistFields,
    "Tag": ChangedTagFields,
    "Venue": ChangedVenueFields,
    "ReleaseEvent": ChangedReleaseEventFields,
    "ReleaseEventSeries": ChangedReleaseEventSeriesFields,
    "Shared": SharedChangedFields,
}  # type: ignore

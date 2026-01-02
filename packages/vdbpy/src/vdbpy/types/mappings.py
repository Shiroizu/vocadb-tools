from vdbpy.config import (
    ALBUM_API_URL,
    ARTIST_API_URL,
    EVENT_API_URL,
    SERIES_API_URL,
    SONG_API_URL,
    TAG_API_URL,
    VENUE_API_URL,
)
from vdbpy.types.changed_fields import ChangedSongFields
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
    EntryType, dict[str, ChangedSongFields]
] = {
    "Song": {
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
}

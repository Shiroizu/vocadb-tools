"""VocaDB version URL helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdbpy.config import WEBSITE
from vdbpy.utils.data import add_s

if TYPE_CHECKING:
    from vdbpy.types.shared import EntryType

_VERSION_PAGE_PATHS: dict[EntryType, str] = {
    "Song": "Song/ViewVersion",
    "Artist": "Artist/ViewVersion",
    "Album": "Album/ViewVersion",
    "Tag": "Tag/ViewVersion",
    "Venue": "Venue/ViewVersion",
    "ReleaseEvent": "Event/ViewVersion",
    "ReleaseEventSeries": "Event/ViewSeriesVersion",
}

_UNSUPPORTED_VERSION_LINK_ENTRY_TYPES = frozenset({"User", "SongList"})


def get_version_link(entry_type: EntryType, version_id: int) -> str | None:
    """Return the ViewVersion page URL for an entry version."""
    if entry_type in _UNSUPPORTED_VERSION_LINK_ENTRY_TYPES:
        return None
    return f"{WEBSITE}/{_VERSION_PAGE_PATHS[entry_type]}/{version_id}"


def get_versions_url(entry_type: EntryType, entry_id: int) -> str:
    """Return the API URL listing all versions of an entry."""
    if entry_type == "User":
        msg = "User entries are not versioned."
        raise ValueError(msg)
    return f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/versions"

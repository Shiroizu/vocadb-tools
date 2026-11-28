"""VocaDB version URL helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

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

_VERSION_HISTORY_PATHS: dict[EntryType, str] = {
    "Song": "Song/Versions",
    "Artist": "Artist/Versions",
    "Album": "Album/Versions",
    "Tag": "Tag/Versions",
    "Venue": "Venue/Versions",
    "ReleaseEvent": "Event/Versions",
    "ReleaseEventSeries": "Event/SeriesVersions",
    "SongList": "SongList/Versions",
}

_UNSUPPORTED_VERSION_LINK_ENTRY_TYPES = frozenset({"User", "SongList"})

type VersionLinkKind = Literal["entry", "version"]

_LINK_KINDS_BY_PATH: dict[str, tuple[EntryType, VersionLinkKind]] = {
    **{
        path.lower(): (entry_type, "version")
        for entry_type, path in _VERSION_PAGE_PATHS.items()
    },
    **{
        path.lower(): (entry_type, "entry")
        for entry_type, path in _VERSION_HISTORY_PATHS.items()
    },
}


def get_version_link(entry_type: EntryType, version_id: int) -> str | None:
    """Return the ViewVersion page URL for an entry version."""
    if entry_type in _UNSUPPORTED_VERSION_LINK_ENTRY_TYPES:
        return None
    return f"{WEBSITE}/{_VERSION_PAGE_PATHS[entry_type]}/{version_id}"


def parse_version_page_link(
    entry_link: str,
) -> tuple[EntryType, VersionLinkKind, int] | None:
    path = entry_link.split("?", maxsplit=1)[0].split("#", maxsplit=1)[0]
    if WEBSITE + "/" in path:
        path = path.split(WEBSITE + "/")[1]
    parts = [part for part in path.strip("/").split("/") if part]
    if len(parts) < 3:
        return None

    prefix, id_str = "/".join(parts[:2]).lower(), parts[2]
    if prefix not in _LINK_KINDS_BY_PATH or not id_str.isdigit():
        return None

    entry_type, kind = _LINK_KINDS_BY_PATH[prefix]
    return (entry_type, kind, int(id_str))


def get_versions_url(entry_type: EntryType, entry_id: int) -> str:
    """Return the API URL listing all versions of an entry."""
    if entry_type == "User":
        msg = "User entries are not versioned."
        raise ValueError(msg)
    return f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/versions"

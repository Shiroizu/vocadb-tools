"""VocaDB version page URL helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdbpy.config import WEBSITE

if TYPE_CHECKING:
    from vdbpy.types.shared import EntryType

_UNSUPPORTED_VERSION_LINK_ENTRY_TYPES = frozenset({"User", "SongList"})


def get_version_link(entry_type: EntryType, version_id: int) -> str | None:
    """Return the ViewVersion page URL for an entry version."""
    if entry_type in _UNSUPPORTED_VERSION_LINK_ENTRY_TYPES:
        return None
    return f"{WEBSITE}/{entry_type}/ViewVersion/{version_id}"

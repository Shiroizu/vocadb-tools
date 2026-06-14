from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from vdbpy.api.entries import is_entry_tagged_1d
from vdbpy.types.albums import AlbumVersion
from vdbpy.types.artists import ArtistVersion
from vdbpy.types.changed_fields import ChangedFields
from vdbpy.types.events import ReleaseEventVersion
from vdbpy.types.series import ReleaseEventSeriesVersion
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.types.songs import SongVersion
from vdbpy.types.tags import TagVersion
from vdbpy.types.venues import VenueVersion

if TYPE_CHECKING:
    from vdbpy.utils.dump import Dump

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

MSG = "All entries require a name, unless tagged with untitled."
FIELDS: list[ChangedFields] = ["Names", "Status"]
ENTRY_TYPES: list[EntryType] = []
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False
TAG_ID = 6335  # Untitled


def _has_name(names: dict, aliases: list[str]) -> bool:
    return any(v.strip() for v in names.values()) or any(v.strip() for v in aliases)


def analyze_dump(dump: Dump) -> set[EntryTuple]:
    violations: set[EntryTuple] = set()

    def _is_untitled(tags) -> bool:
        return any(usage.tag and usage.tag.id == TAG_ID for usage in tags)

    for song in dump.songs():
        if not _has_name(song.names, song.aliases) and not _is_untitled(song.tags):
            violations.add(("Song", song.id))

    for album in dump.albums():
        if not _has_name(album.names, album.aliases) and not _is_untitled(album.tags):
            violations.add(("Album", album.id))

    for artist in dump.artists():
        if not _has_name(artist.names, artist.aliases) and not _is_untitled(
            artist.tags,
        ):
            violations.add(("Artist", artist.id))

    for event in dump.events():
        if not _has_name(event.names, event.aliases) and not _is_untitled(event.tags):
            violations.add(("ReleaseEvent", event.id))

    for series in dump.event_series():
        if not _has_name(series.names, series.aliases) and not _is_untitled(
            series.tags,
        ):
            violations.add(("ReleaseEventSeries", series.id))

    for tag in dump.tags():
        if not _has_name(tag.names, tag.aliases):
            violations.add(("Tag", tag.id))

    return violations


def _entry_tuple(version_data: BaseEntryVersion) -> EntryTuple | None:
    match version_data:
        case SongVersion():
            return ("Song", version_data.entry_id)
        case AlbumVersion():
            return ("Album", version_data.entry_id)
        case ArtistVersion():
            return ("Artist", version_data.entry_id)
        case ReleaseEventVersion():
            return ("ReleaseEvent", version_data.entry_id)
        case ReleaseEventSeriesVersion():
            return ("ReleaseEventSeries", version_data.entry_id)
        case TagVersion():
            return ("Tag", version_data.entry_id)
        case VenueVersion():
            return ("Venue", version_data.entry_id)
        case _:
            return None


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    has_name = any(
        name.strip()
        for name in [
            version_data.name_english,
            version_data.name_non_english,
            version_data.name_romaji,
            *version_data.aliases,
        ]
    )

    if has_name:
        return "Not applicable"

    entry = _entry_tuple(version_data)
    if entry and is_entry_tagged_1d(entry, TAG_ID):
        return "Valid"

    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [],
        "Not applicable": [],
        "Rule violation": [],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {}
    return edit_check_tests, entry_check_tests

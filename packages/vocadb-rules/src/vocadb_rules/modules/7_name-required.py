from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import func, select
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
    from vdbpy.utils.dump_sql import DumpDB

from vocadb_rules.mod_types import (
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


def analyze_sql_dump(db: DumpDB) -> set[EntryTuple]:
    entities: list[tuple[Any, EntryType]] = [
        (db.Song, "Song"),
        (db.Album, "Album"),
        (db.Artist, "Artist"),
        (db.Event, "ReleaseEvent"),
        (db.EventSeries, "ReleaseEventSeries"),
        (db.Tag, "Tag"),
    ]
    violations: set[EntryTuple] = set()
    for entity, entry_type in entities:
        has_name = (
            select(db.EntryName.pk)
            .where(
                db.EntryName.entry_type == entry_type,
                db.EntryName.entry_id == entity.id,
                func.trim(db.EntryName.value) != "",
            )
            .exists()
        )
        is_untitled = (
            select(db.EntryTag.pk)
            .where(
                db.EntryTag.entry_type == entry_type,
                db.EntryTag.entry_id == entity.id,
                db.EntryTag.tag_id == TAG_ID,
            )
            .exists()
        )
        ids = db.scalars(select(entity.id).where(~has_name, ~is_untitled))
        violations.update((entry_type, entry_id) for entry_id in ids)
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

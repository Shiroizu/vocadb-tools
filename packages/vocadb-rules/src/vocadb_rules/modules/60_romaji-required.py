from typing import Literal

from vdbpy.types.albums import AlbumVersion
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryType
from vdbpy.types.songs import SongVersion

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

MSG = "Approved album/song entries should include the romanized title (if applicable)."
FIELDS: list[ChangedFields] = ["Names", "Status", "OriginalName"]
ENTRY_TYPES: list[EntryType] = ["Album", "Song"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False
ASSUME_VALID_FOR_RULE_ID: list[int] = [24]


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, (AlbumVersion, SongVersion)):
        return "Wrong entry type"

    if version_data.status != "Approved":
        return "Not applicable"

    if version_data.default_name_language != "Non-English":
        return "Not applicable"

    if not version_data.name_non_english:
        return "Not applicable"

    if version_data.name_romaji:
        return "Valid"

    if version_data.name_english:
        # Assuming full loanword translation
        return "Not applicable"

    return "Rule violation"


# Disabled for better performance
# def find_relevant_entries(save_dir: Path) -> set[EntryTuple]:
#    approved_album_entries: set[EntryTuple] = set(
#        get_saved_entry_search(
#            save_dir / "approved-album-entries.csv",
#            ALBUM_API_URL,
#            {"status": "Approved"},
#        )[0]
#    )
#    approved_song_entries: set[EntryTuple] = set(
#        get_saved_entry_search(
#            save_dir / "approved-song-entries.csv",
#            SONG_API_URL,
#            {"status": "Approved"},
#        )[0]
#    )
#    return approved_album_entries | approved_song_entries


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Album", 20118, 118568)],
        "Rule violation": [("Song", 1, 2897822), ("Album", 51672, 272801)],
        "Not applicable": [("Song", 829266, 2780979), ("Song", 803468, 3039854)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(118568, 12134, ("Album", 20118, 118568))],
        "Rule violation": [(272801, 329, ("Album", 51672, 272801))],
        "Not applicable": [(2780979, 29853, ("Song", 829266, 2780979))],
        "Wrong entry type": [(0, 0, ("Artist", 106476, 585128))],
    }
    return edit_check_tests, entry_check_tests

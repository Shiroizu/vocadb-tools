from pathlib import Path

from vdbpy.api.entries import get_saved_entry_search
from vdbpy.api.songs import get_song_by_id
from vdbpy.config import SONG_API_URL
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import (
    BaseEntryVersion,
    EntryTuple,
    EntryType,
)
from vdbpy.types.songs import OptionalSongFieldName, SongEntry, SongVersion
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CheckResult,
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
)

logger = get_logger()

MSG = "Song entries should include a source: link/description/album."
FIELDS: list[ChangedFields] = ["WebLinks", "Notes", "PVs"]
ENTRY_TYPES: list[EntryType] = ["Song"]
COMPLETE = True
AUTOMATICALLY_FIXED = False


def find_relevant_entries(save_dir: Path) -> set[EntryTuple]:
    params = {
        "advancedFilters[0][description]": "Standalone (no album)",
        "advancedFilters[0][filterType]": "HasAlbum",
        "advancedFilters[0][negate]": True,
        "advancedFilters[0][param]": "",
        "advancedFilters[1][description]": "No media",
        "advancedFilters[1][filterType]": "HasMedia",
        "advancedFilters[1][negate]": True,
        "advancedFilters[1][param]": "",
    }
    return set(
        get_saved_entry_search(
            save_dir / "songs_without_album_or_pvs.csv",
            SONG_API_URL,
            params,
        )[0],
    )


def check_entry_version_for_rule(
    version_data: BaseEntryVersion, is_relevant_entry: bool | None = None,
) -> CheckResult:
    if not isinstance(version_data, SongVersion):
        return "Wrong entry type"

    if (
        version_data.external_links
        or version_data.description
        or version_data.description_eng
        or version_data.pvs
    ):
        return "Valid"

    if is_relevant_entry:  # no albums
        return "Rule violation"
    included_fields: set[OptionalSongFieldName] = {"albums"}
    logger.warning("Fetching song entry without cache...")
    song_entry: SongEntry = get_song_by_id(
        song_id=version_data.entry_id,
        fields=included_fields,
    )
    assert song_entry.albums != "Unknown"
    if song_entry.albums:
        return "Valid"
    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Song", 647767, 2097723)],
        "Rule violation": [("Song", 295171, 882866)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {}
    return edit_check_tests, entry_check_tests

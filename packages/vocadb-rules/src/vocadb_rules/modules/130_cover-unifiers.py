from pathlib import Path
from typing import Literal

from vdbpy.api.entries import (
    get_saved_entry_search,
    is_entry_tagged_1d,
)
from vdbpy.api.songs import get_songs
from vdbpy.config import SONG_API_URL
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import (
    BaseEntryVersion,
    EntryTuple,
    EntryType,
)
from vdbpy.types.songs import SongSearchParams, SongVersion
from vdbpy.utils.cache import cache_conditionally
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Cover unifier entries require 5+ derived versions."
FIELDS: list[ChangedFields] = []
ENTRY_TYPES: list[EntryType] = ["Song"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False
TAG_ID = 6751

def find_relevant_entries(save_dir: Path) -> set[EntryTuple]:
    return set(
        get_saved_entry_search(
            save_dir / "cover_unifier_entries.csv",
            SONG_API_URL,
            {"tagId[]": TAG_ID},
        )[0],
    )


@cache_conditionally(days=0.1)
def has_more_than_5_derived_versions(entry_id: int) -> bool:
    derived_versions = get_songs(
        song_search_params=SongSearchParams(original_version_id=entry_id, max_results=5),
    )
    return len(derived_versions) >= 5


def check_entry_version_for_rule(
    version_data: BaseEntryVersion, is_relevant_entry: bool | None = None,
) -> RuleModuleResult:
    if not isinstance(version_data, SongVersion):
        return "Wrong entry type"

    is_tagged = (
        True
        if is_relevant_entry
        else is_entry_tagged_1d(("Song", version_data.entry_id), TAG_ID)
    )

    if not is_tagged:
        return "Not applicable"

    if has_more_than_5_derived_versions(version_data.entry_id):
        return "Valid"

    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Song", 857671, 2905980),
            ("Song", 857421, 2904987),
            ("Song", 859216, 2910602),
        ],
        "Not applicable": [("Song", 886353, 3008705)],
        "Rule violation": [("Song", 889898, 3020190)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(863765, 14763, ("Song", 289036, 2042277))],
        "Wrong entry type": [(0, 0, ("Artist", 106476, 585128))],
        "Rule violation": [(3020190, 329, ("Song", 889898, 3020191))],
        "Not applicable": [(3008023, 33835, ("Song", 886353, 3008705))],
    }
    return edit_check_tests, entry_check_tests

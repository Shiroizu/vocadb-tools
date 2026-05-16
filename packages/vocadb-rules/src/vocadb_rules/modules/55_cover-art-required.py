from pathlib import Path
from typing import Literal

from vdbpy.api.entries import (
    get_saved_entry_search,
    is_entry_tagged_1d,
)
from vdbpy.config import ALBUM_API_URL
from vdbpy.types.albums import AlbumVersion
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import (
    BaseEntryVersion,
    EntryTuple,
    EntryType,
)
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()


MSG = "Finished album entries require cover art or the 'no cover art' tag"
FIELDS: list[ChangedFields] = ["Cover", "Status"]
ENTRY_TYPES: list[EntryType] = ["Album"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False
TAG_ID = 2811


def find_relevant_entries(save_dir: Path) -> set[EntryTuple]:
    # Advanced filters don't seem to work with tag negations

    params = {
        "advancedFilters[0][description]": "No+cover+picture",
        "advancedFilters[0][filterType]": "NoCoverPicture",
        "advancedFilters[0][negate]": False,
        "advancedFilters[0][param]": "",
        "status": "Finished",
        "fields": "Tags",
    }
    finished_entries_with_no_cover_art_advanced_filter = get_saved_entry_search(
        save_dir / "no-cover-art-adv-filter.csv",
        ALBUM_API_URL,
        params,
    )[0]

    params = {"tagId[]": 2811, "status": "Finished"}
    finished_entries_tagged_with_no_cover_art = get_saved_entry_search(
        save_dir / "no-cover-art-tagged.csv",
        ALBUM_API_URL,
        params,
    )[0]

    return {
        (entry[0], entry[1])
        for entry in finished_entries_with_no_cover_art_advanced_filter
    } - {
        (entry[0], entry[1])
        for entry in finished_entries_tagged_with_no_cover_art
    }


def check_entry_version_for_rule(
    version_data: BaseEntryVersion, is_relevant_entry: bool | None = None,
) -> RuleModuleResult:
    if not isinstance(version_data, AlbumVersion):
        return "Wrong entry type"

    if version_data.status == "Draft":
        return "Not applicable"

    is_tagged = (
        False
        if is_relevant_entry
        else is_entry_tagged_1d(("Album", version_data.entry_id), TAG_ID)
    )
    if version_data.picture_mime or is_tagged:
        return "Valid"

    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Album", 27837, 110457), ("Album", 9439, 35502)],
        "Rule violation": [("Album", 49376, 251361)],
        "Not applicable": [("Album", 43566, 207656)],
    }
    # - 55: ['Not applicable', 'Rule violation', 'Valid', 'Wrong entry type']
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(110457, 11035, ("Album", 27837, 110457))],
        "Rule violation": [(251361, 24565, ("Album", 49376, 251361))],
        "Not applicable": [(207656, 11713, ("Album", 43566, 207656))],
        "Wrong entry type": [(0, 0, ("Song", 809916, 2694694))],
    }
    return edit_check_tests, entry_check_tests

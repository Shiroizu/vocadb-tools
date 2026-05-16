from pathlib import Path
from typing import Any, Literal

import requests
from vdbpy.api.entries import get_saved_entry_search
from vdbpy.config import SONG_API_URL
from vdbpy.edit.entries import edit_entry
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.types.songs import SongVersion
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Short message for the entry report"
FIELDS: list[ChangedFields] = []  # used for skipping irrelevant edits
ENTRY_TYPES: list[EntryType] | Literal["All"] = []  # skip irrelevant entry types
# TODO assert Nonempty!!
COMPLETE = True  # whether the rule check is complete/exhaustive or not
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = "Partially"
ASSUME_VALID_FOR_RULE_ID: list[int] = []

TAG_ID = 0 # Use this in conjunction with find_relevant_entries()
           # and add 'is_relevant_entry: bool | None = None'
           # to 'check_entry_version_for_rule()'

def find_relevant_entries(save_dir: Path) -> set[EntryTuple]:
    # Use this for improved performance whenever possible
    # Using get_saved_entry_search is recommended if lots of results
    return set(
        get_saved_entry_search(
            save_dir / f"songs_tagged_with_{TAG_ID}.csv",
            SONG_API_URL,
            {"tagId[]": TAG_ID},
        )[0],
    )


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    # Filter entry types if necessary
    if not isinstance(version_data, SongVersion):
        return "Wrong entry type"

    if not version_data.lyrics:
        # Not applicable in this version, but version data had to download to confirm
        return "Not applicable"

    for lyric in version_data.lyrics:
        if not lyric.source and not lyric.url:
            return "Rule violation"
    return "Valid"  # User added or edited data in a valid way

    # Possible rule violation
    # = Manual mod verification required before sending the report


def test() -> CorrectTestResults:
    # Some (deleted) test entries
    # - https://vocadb.net/S/889898
    # - https://vocadb.net/Al/51672
    # - https://vocadb.net/Ar/72959
    # - https://vocadb.net/E/9772
    # - https://vocadb.net/Es/1041
    # - https://vocadb.net/Venue/Details/433
    # - https://vocadb.net/T/6366
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [],
        "Not applicable": [("Song", 1, 2893028)],
        "Rule violation": [],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        # "Valid": [(relevant_v_id, relevant_u_id, (entry_type, e_id, v_id))],
        # ... (run '... --test' to check for missing tests)
    }
    return edit_check_tests, entry_check_tests


def autofix(
    session: requests.Session,
    entry: EntryTuple,
    base_update_note: str = "",
    prompt: bool = True,
    args: Any = None,
) -> bool:
    return edit_entry(
        session=session,
        entry=entry,
        edit_function=my_edit_function,
        base_update_note=base_update_note,
        prompt=prompt,
        args=args,
    )


def my_edit_function(
    data: dict[Any, Any], base_update_note: str, arg: Any,
) -> dict[Any, Any]:
    if not arg:
        return {}

    update_notes: str = "Fixed something."
    data = my_helper_function_7d(data)
    if not data:
        return {}

    something_fixed = False
    field_items_to_keep: list[Any] = []
    for field_item in data["fieldName"]:
        if not field_item["source"]:
            field_item["source"] = "Source is xyz"
            something_fixed = True
        field_items_to_keep.append(field_item)

    if not something_fixed:
        return {}

    data["fieldName"] = field_items_to_keep
    data["updateNotes"] = base_update_note + update_notes
    return data


# helper function for autofix
@cache_with_expiration(days=7)
def my_helper_function_7d(data: dict[Any, Any]) -> list[int]:
    logger.info(data)
    return [1, 2, 3]

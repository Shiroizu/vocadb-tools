from typing import Literal

from vdbpy.config import TAG_API_URL
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.types.tags import TagVersion
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "All tags should specify the tag category."
FIELDS: list[ChangedFields] = ["CategoryName"]
ENTRY_TYPES: list[EntryType] = ["Tag"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False


def check_entry_version_for_rule(
    version_data: BaseEntryVersion,
    is_relevant_entry = None,
    # needed since currently param is supplied if
    # find_relevant_entries() is present (TODO FIX)
) -> RuleModuleResult:
    if not isinstance(version_data, TagVersion):
        return "Wrong entry type"

    if not version_data.tag_category:
        return "Rule violation"

    return "Valid"


def find_relevant_entries(save_dir) -> set[EntryTuple]:
    url = f"{TAG_API_URL}/by-categories"
    tags_by_category = fetch_json(url)
    last_category = tags_by_category[-1]
    if not last_category["name"]:
        tag_entries: set[EntryTuple] = set()
        for tag in last_category["tags"]:
            tag_entry_tuple = ("Tag", tag["id"])
            tag_entries.add(tag_entry_tuple)
        return tag_entries
    return set()


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Tag", 6063, 33210)],
        "Rule violation": [("Tag", 12422, 57230)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {}
    return edit_check_tests, entry_check_tests

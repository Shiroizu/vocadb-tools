from typing import Literal

from vdbpy.types.artists import ArtistVersion
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import (
    BaseEntryVersion,
    EntryType,
)

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

MSG = "P-name duplicates are redundant."
FIELDS: list[ChangedFields] = ["Names", "Status"]
ENTRY_TYPES: list[EntryType] = ["Artist"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False
ASSUME_VALID_FOR_RULE_ID: list[int] = [8]


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, ArtistVersion):
        return "Wrong entry type"

    if version_data.status == "Draft":
        # Draft since 8 are draft
        # otherwise issue with Song v1864789 for example
        return "Not applicable"

    names: list[str] = []
    p_name_found = False

    all_names = [
        version_data.name_english,
        version_data.name_non_english,
        version_data.name_romaji,
        *version_data.aliases,
    ]

    for name in all_names:
        if name.strip():
            if name.lower().endswith("p"):
                names.append(name.lower().strip().rstrip("-p"))
                p_name_found = True
            else:
                names.append(name.lower().strip())

    if not p_name_found:
        return "Not applicable"

    if len(names) != len(set(names)):
        return "Rule violation"

    return "Valid"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Artist", 674, 21194), ("Artist", 175, 60915)],
        "Rule violation": [("Artist", 674, 311520)],
        "Not applicable": [("Artist", 20, 28495)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(21194, 149, ("Artist", 674, 21194))],
        "Rule violation": [(311520, 8720, ("Artist", 674, 311520))],
        "Not applicable": [(551776, 28301, ("Artist", 166431, 551776))],
        "Wrong entry type": [(0, 0, ("Song", 809916, 2694694))],
    }
    return edit_check_tests, entry_check_tests

from typing import Literal

from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryType
from vdbpy.types.tags import TagVersion

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

MSG = "Tags should include a description."
FIELDS: list[ChangedFields] = ["Description"]
ENTRY_TYPES: list[EntryType] = ["Tag"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, TagVersion):
        return "Wrong entry type"

    if version_data.description:
        return "Valid"
    if version_data.description_eng:
        return "Valid"
    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Tag", 6366, 55112),
        ],
        "Rule violation": [("Tag", 6366, 55359)],
    }
    # - 150: ['Rule violation', 'Valid', 'Wrong entry type']

    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(55112, 329, ("Tag", 6366, 55112))],
        "Rule violation": [(55359, 329, ("Tag", 6366, 55359))],
        "Wrong entry type": [(0, 0, ("Album", 32890, 137927))],
    }
    return edit_check_tests, entry_check_tests

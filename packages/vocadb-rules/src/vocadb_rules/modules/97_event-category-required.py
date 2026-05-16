from typing import Literal

from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.events import ReleaseEventVersion
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

MSG = "Event entries require a category."
FIELDS: list[ChangedFields] = ["Category", "Series"]
ENTRY_TYPES: list[EntryType] = ["ReleaseEvent"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, ReleaseEventVersion):
        return "Wrong entry type"

    if version_data.event_category and version_data.event_category != "Unspecified":
        return "Valid"

    if version_data.series:
        return "Not applicable"

    return "Rule violation"


def test() -> CorrectTestResults:
    # Two types of events:
    # 1) standalone
    # 2) series events
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("ReleaseEvent", 6508, 26142),  # standalone
        ],
        "Rule violation": [
            ("ReleaseEvent", 9772, 40347),  # standalone
        ],
        "Not applicable": [
            ("ReleaseEvent", 9772, 41528),  # series
        ],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(26384, 149, ("ReleaseEvent", 7199, 28844))],
        "Not applicable": [(41528, 329, ("ReleaseEvent", 9772, 41528))],
        "Rule violation": [(40347, 329, ("ReleaseEvent", 9772, 40347))],
        "Wrong entry type": [(0, 0, ("Artist", 106476, 585128))],
    }
    return edit_check_tests, entry_check_tests

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

MSG = "Artist entries require an external link or a description."
FIELDS: list[ChangedFields] = ["WebLinks", "Description"]
ENTRY_TYPES: list[EntryType] = ["Artist"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, ArtistVersion):
        return "Wrong entry type"

    if (
        version_data.external_links
        or version_data.description
        or version_data.description_eng
    ):
        return "Valid"

    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Artist", 61973, 147929)],
        "Rule violation": [("Artist",135608, 421184)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
    }
    return edit_check_tests, entry_check_tests

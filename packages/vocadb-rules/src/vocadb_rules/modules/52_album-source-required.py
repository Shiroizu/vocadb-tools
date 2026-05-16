from typing import Literal

from vdbpy.types.albums import AlbumVersion
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryType
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Album entries must include a PV link, external link or description."
ENTRY_TYPES: list[EntryType] = ["Album"]
FIELDS: list[ChangedFields] = [
    "Description",
    "PVs",
    "WebLinks",
]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, AlbumVersion):
        return "Wrong entry type"

    if (
        version_data.pvs
        or version_data.external_links
        or version_data.description
        or version_data.description_eng
    ):
        return "Valid"

    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Album", 49662, 253317),
            ("Album", 49656, 253301),
            ("Album", 24397, 253319),
            ("Album", 50521, 258278),
        ],
        "Rule violation": [("Album", 30343, 254842)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(258276, 1083, ("Album", 50521, 258278))],
        "Rule violation": [(258274, 1083, ("Album", 50521, 258274))],
        "Wrong entry type": [(0, 0, ("Artist", 106476, 585128))],
    }
    return edit_check_tests, entry_check_tests

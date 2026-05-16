from typing import Literal, get_args

from vdbpy.types.artists import ArtistVersion, VoicebankType
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

MSG = "Voicebank release date must be specified."
FIELDS: list[ChangedFields] = ["Names", "ReleaseDate", "ArtistType", "Status"]
ENTRY_TYPES: list[EntryType] = ["Artist"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, ArtistVersion):
        return "Wrong entry type"

    if version_data.status == "Draft":
        return "Not applicable"

    if version_data.artist_type not in get_args(VoicebankType):
        return "Not applicable"

    if (
        version_data.name_non_english.lower().endswith("(unknown)")
        or version_data.name_romaji.lower().endswith("(unknown)")
        or version_data.name_english.lower().endswith("(unknown)")
    ):
        return "Not applicable"

    if version_data.vb_release_date:
        return "Valid"

    return "Rule violation"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Artist", 25214, 394417)],
        "Rule violation": [("Artist", 84860, 228018)],
        "Not applicable": [("Artist", 64424, 394129)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Rule violation": [(593852, 1002, ("Artist", 174807, 594389))],
        "Not applicable": [(394129, 25365, ("Artist", 64424, 394129))],
        "Valid": [(394417, 26858, ("Artist", 25214, 394417))],
        "Wrong entry type": [(0, 0, ("Album", 32890, 137927))],
    }
    return edit_check_tests, entry_check_tests

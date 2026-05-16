
from typing import Any, Literal

import requests
from vdbpy.edit.entries import edit_entry
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.events import ReleaseEventVersion
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
    EntryTypesWithoutVersionedStatus,
    RuleModuleResult,
)

logger = get_logger()
MSG = "Original language field for entry names should not be 'unspecified' for 'finished' entries."
FIELDS: list[ChangedFields] = ["OriginalName", "Status", "Series"]
ENTRY_TYPES: list[EntryType] = []
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = "Partially"


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if version_data.status == "Draft":
        if not isinstance(version_data, tuple(EntryTypesWithoutVersionedStatus)):
            return "Not applicable"

    if version_data.default_name_language == "Unspecified":
        if isinstance(version_data, ReleaseEventVersion) and version_data.series:
            # TODO fix if custom name https://vocadb.net/E/9900
            return "Not applicable"

        return "Rule violation"

    return "Valid"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Song", 1, 2893020),
            ("Album", 51672, 271716),
            ("Artist", 72959, 598898),
            ("ReleaseEvent", 9772, 41642),
            ("ReleaseEventSeries", 1041, 3838),
            ("Tag", 6366, 57270),
            ("Venue", 433, 1110),
        ],
        "Rule violation": [
            ("Song", 1, 2893019),
            ("Album", 51672, 271717),
            ("Artist", 72959, 598899),
            ("ReleaseEvent", 9772, 41643),
            ("ReleaseEventSeries", 1041, 3839),
            ("Tag", 6366, 57271),
            ("Venue", 433, 1106),
        ],
        "Not applicable": [
            ("Song", 1, 2855022),
            ("Album", 51672, 271511),
            ("Artist", 72959, 598867),
            ("Tag", 6366, 17002),
        ],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [
            (3020683, 329, ("Song", 889898, 3020683)),
            (271716, 31074, ("Album", 51672, 271716)),
            (598898, 31074, ("Artist", 72959, 598898)),
            (41642, 31074, ("ReleaseEvent", 9772, 41642)),
            (3838, 31074, ("ReleaseEventSeries", 1041, 3838)),
            (57270, 31074, ("Tag", 6366, 57270)),
            (1110, 31074, ("Venue", 433, 1110)),
        ],
        "Rule violation": [
            (3020682, 329, ("Song", 889898, 3020682)),
            (271717, 31074, ("Album", 51672, 271717)),
            (598899, 31074, ("Artist", 72959, 598899)),
            (41643, 31074, ("ReleaseEvent", 9772, 41643)),
            (3839, 31074, ("ReleaseEventSeries", 1041, 3839)),
            (57271, 31074, ("Tag", 6366, 57271)),
            (1106, 31074, ("Venue", 433, 1109)),
        ],
        "Not applicable": [
            (3020190, 329, ("Song", 889898, 3020190)),
            (271511, 31074, ("Album", 51672, 271511)),
            (598867, 31074, ("Artist", 72959, 598867)),
            (17002, 8374, ("Tag", 6366, 17002)),
        ],
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
        edit_function=specify_default_name_language,
        prompt=prompt,
        base_update_note=base_update_note,
        args=args,
    )


def specify_default_name_language(
    data: dict[Any, Any], base_update_note: str = "", args: Any = None,
) -> dict[Any, Any]:
    # not supported for ReleaseEvents
    if data["defaultNameLanguage"] != "Unspecified":
        logger.warning("Default name language is already fixed")
        _ = input("Press enter to continue")
        return {}

    if len(data["names"]) > 1:
        logger.info("Found more than 1 names:")
        for name in data["names"]:
            logger.info(f"- {name['language']}: {name['value']}")
        return {}

    name_language = data["names"][0]["language"]
    if name_language == "Unspecified":
        logger.info(f"Name language for '{data['names'][0]['value']}' is 'Unspecified'")
        return {}
    data["defaultNameLanguage"] = name_language

    name_language = "Non-English" if name_language == "Japanese" else name_language
    logger.info(f"{name_language}: {data['names'][0]['value']}")

    update_notes = (
        f"Changed default name language to match the existing name ({name_language})"
    )
    data["updateNotes"] = base_update_note + update_notes
    return data

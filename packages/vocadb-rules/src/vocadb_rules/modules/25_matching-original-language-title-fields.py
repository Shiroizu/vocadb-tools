
from typing import Any, Literal

import requests
from vdbpy.edit.entries import edit_entry
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
    EntryTypesWithoutVersionedStatus,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Default name language should match with the given primary name field."
FIELDS: list[ChangedFields] = ["OriginalName", "Names", "Status"]
ENTRY_TYPES: list[EntryType] = []
COMPLETE = False
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = "Partially"
ASSUME_VALID_FOR_RULE_ID: list[int] = [24]


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if version_data.status == "Draft":
        if not isinstance(version_data, tuple(EntryTypesWithoutVersionedStatus)):
            return "Not applicable"

    all_names: list[str] = [
        version_data.name_english,
        version_data.name_non_english,
        version_data.name_romaji,
    ]

    names: list[str] = []
    for name in all_names:
        stripped = name.strip()
        if stripped:
            names.append(stripped)

    if not names:
        return "Not applicable"

    possibly_untitled = all(len(name) < 2 for name in names)
    # Assume invisible chars with T/untitled

    match version_data.default_name_language:
        case "Non-English":
            if not version_data.name_non_english:
                if not possibly_untitled:
                    return "Rule violation"
        case "Romaji":
            if not version_data.name_romaji:
                if not possibly_untitled:
                    return "Rule violation"
        case "English":
            if not version_data.name_english:
                if not possibly_untitled:
                    return "Rule violation"
        case "Unspecified":
            if not possibly_untitled:
                return "Rule violation"
                # Dupe check for rule 24

    return "Valid"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Song", 408226, 1275586),
            ("Album", 30514, 125117),
            ("Artist", 72959, 599629),
            ("ReleaseEvent", 9772, 41657),
            ("ReleaseEvent", 9772, 41664),
            ("ReleaseEvent", 9772, 41652),
            ("ReleaseEventSeries", 1041, 3843),
            ("Venue", 433, 1111),  # Draft status
            ("Venue", 433, 1117),
            ("Tag", 6366, 57328),
        ],
        "Rule violation": [
            ("Song", 1, 2897813),
            ("Album", 51672, 272204),
            ("Artist", 72959, 599628),
            ("ReleaseEvent", 9772, 41653),  # Standalone event
            ("ReleaseEventSeries", 1041, 3844),
            ("Venue", 433, 1118),
            ("Tag", 6366, 57329),
        ],
        "Not applicable": [
            ("Song", 222185, 2559665),  # Invisible characters
            ("Song", 889898, 3038456),  # Draft status
            ("Album", 36347, 157190),  # Invisible characters
            ("Album", 51672, 272216),  # Draft status
            ("Artist", 72959, 599652),  # Invisible characters
            ("Artist", 72959, 599632),  # Draft status
            ("ReleaseEvent", 9772, 41651),  # Standalone event, invisible characters
            ("ReleaseEventSeries", 1041, 3847),
            ("Venue", 433, 1120),  # Invisible characters
            ("Tag", 6366, 57343),  # Invisible characters
            ("Tag", 6366, 57331),  # Draft status
        ],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [
            (1275586, 1083, ("Song", 408226, 1275586)),
            (125117, 12056, ("Album", 30514, 125117)),
            (599629, 31074, ("Artist", 72959, 599629)),
            (41650, 31074, ("ReleaseEvent", 9772, 41650)),
            (3843, 31074, ("ReleaseEventSeries", 1041, 3843)),
            (1117, 31074, ("Venue", 433, 1117)),
            (1111, 31074, ("Venue", 433, 1111)),
            (57328, 31074, ("Tag", 6366, 57328)),
        ],
        "Rule violation": [
            (3020698, 329, ("Song", 889898, 3020698)),
            (271717, 31074, ("Album", 51672, 272204)),
            (598907, 31074, ("Artist", 72959, 599628)),
            (41653, 31074, ("ReleaseEvent", 9772, 41653)),
            (3844, 31074, ("ReleaseEventSeries", 1041, 3844)),
            (1118, 31074, ("Venue", 433, 1118)),
            (57329, 31074, ("Tag", 6366, 57329)),
        ],
        "Not applicable": [
            (2559665, 28818, ("Song", 222185, 2559665)),
            (157190, 1083, ("Album", 36347, 157190)),
            (599652, 31074, ("Artist", 72959, 599652)),
            (41651, 31074, ("ReleaseEvent", 9772, 41651)),
            (3847, 31074, ("ReleaseEventSeries", 1041, 3847)),
            (57343, 31074, ("Tag", 6366, 57343)),
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
        edit_function=fix_default_name_language,
        prompt=prompt,
        base_update_note=base_update_note,
        args=args,
    )


def fix_default_name_language(
    data: dict[Any, Any], base_update_note: str = "", args: Any = None,
) -> dict[Any, Any]:
    # TODO full tests
    # not supported for ReleaseEvents

    assert data["defaultNameLanguage"] != "Unspecified", (
        "Rule 25 assumes rule 24 (original language required)"
    )

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
        "Changed default name language to match the existing"
        f" name field ({name_language})"
    )
    data["updateNotes"] = base_update_note + update_notes
    return data

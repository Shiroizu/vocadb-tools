
from typing import Any, Literal

import requests
from vdbpy.edit.entries import edit_entry
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.events import ReleaseEventVersion
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    EntryTypesWithoutVersionedStatus,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Names should not be duplicated."
FIELDS: list[ChangedFields] = ["Names", "Status"]
ENTRY_TYPES: list[EntryType] = []
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = "Partially"
ASSUME_VALID_FOR_RULE_ID: list[int] = [25]


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if version_data.status == "Draft":
        # Draft since 24 & 25 are draft
        # otherwise issue with Song v1864789 for example
        if not isinstance(version_data, EntryTypesWithoutVersionedStatus):
            return "Not applicable"

    if isinstance(version_data, ReleaseEventVersion):
        # Automatically valid since dupe event names are blocked
        return "Valid"

    names: list[str] = []

    for name in [
        version_data.name_english,
        version_data.name_non_english,
        version_data.name_romaji,
        *version_data.aliases,
    ]:
        if name.strip():
            names.append(name.strip())

    if len(names) != len(set(names)):
        return "Rule violation"

    return "Valid"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Song", 1501, 2752223)],
        "Not applicable": [("Song", 1, 2893016)],
        "Rule violation": [
            ("Song", 1, 3019936),
            ("Artist", 72959, 599793),
            ("Album", 51672, 272265),
            ("Tag", 6366, 57367),
            ("ReleaseEventSeries", 1041, 3849),
            ("Venue", 433, 1122),
        ],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(3020682, 329, ("Song", 889898, 3020682))],
        "Not applicable": [(3020723, 329, ("Song", 889898, 3020723))],
        "Rule violation": [(3020724, 329, ("Song", 889898, 3020724))],
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
        edit_function=remove_duplicate_names,
        prompt=prompt,
        base_update_note=base_update_note,
        args=args,
    )


def remove_duplicate_names(
    data: dict[Any, Any], base_update_note: str = "", args: Any = None,
) -> dict[Any, Any]:
    # TODO full tests
    # "defaultNameLanguage":"Japanese",
    # [
    #   {"id":233489,"language":"Japanese","value":"Yab."},
    #   {"id":233490,"language":"Romaji","value":"Yaba"}
    #   {"id":233205,"language":"English","value":"Yab."},
    # ],
    #
    # fix possible https://vocadb.net/Artist/ViewVersion/394972
    # fix not possible https://vocadb.net/Song/ViewVersion/902821

    update_notes: str = "Removed duplicate name(s):"

    dnl = data["defaultNameLanguage"]
    assert dnl != "Unspecified"  # rule 24

    original_name: str = ""
    for name in data["names"]:
        if name["language"] == dnl:
            original_name = name["value"].strip()
            break

    assert original_name  # rule 25

    logger.debug(f"Original name is '{original_name}' ({dnl})")

    names_to_keep: list[Any] = []
    edited_something: bool = False
    for name in data["names"]:
        if name["language"] == dnl:
            names_to_keep.append(name)
            continue

        if name["value"].strip() == original_name:
            language = (
                "Alias" if name["language"] == "Unspecified" else name["language"]
            )
            logger.debug(f"Removing duplicate name '{original_name}' {language}")
            update_notes += f' "{name["value"]}" ({language})'
            edited_something = True
            continue

        names_to_keep.append(name)

    data["updateNotes"] = base_update_note + update_notes

    if names_to_keep:
        data["names"] = names_to_keep
    if not edited_something:
        data = {}

    return data

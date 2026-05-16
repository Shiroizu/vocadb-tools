
from typing import Any, Literal, get_args

import requests
from vdbpy.edit.entries import edit_entry
from vdbpy.types.artists import ArtistVersion, VoicebankType
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Specify character designer only if it's different from the illustrator."
FIELDS: list[ChangedFields] = ["Groups", "ArtistType"]
ENTRY_TYPES: list[EntryType] = ["Artist"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = True


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, ArtistVersion):
        return "Wrong entry type"

    if version_data.artist_type not in get_args(VoicebankType):
        return "Not applicable"

    i = version_data.vb_chara_designer_ids
    d = version_data.vb_illustrator_ids

    if not i and not d:
        return "Not applicable"

    if not i or not d:
        return "Valid"

    if len(i) > 1 or len(d) > 1:
        # Makes sense to be specific if multiple artists
        # TODO clarify on wiki
        return "Valid"

    if i[0] == d[0]:
        return "Rule violation"

    return "Valid"


def test() -> CorrectTestResults:
    # Two types of vbs:
    # 1) Root
    # 2) Derived
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Artist", 169183, 565072),
            ("Artist", 84432, 378974),
            ("Artist", 155252, 519415),
        ],
        "Not applicable": [("Artist", 65919, 161959)],
        "Rule violation": [("Artist", 175354, 596267)],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(367127, 1083, ("Artist", 84432, 378974))],
        "Not applicable": [(161960, 10677, ("Artist", 65919, 168772))],
        "Rule violation": [(596267, 29529, ("Artist", 175354, 596267))],
        "Wrong entry type": [(0, 0, ("Album", 32890, 137927))],
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
        edit_function=remove_redundant_character_designer_credit,
        base_update_note=base_update_note,
        prompt=prompt,
        args=None,
    )


def remove_redundant_character_designer_credit(
    data: dict[Any, Any], base_update_note: str, args: Any = None,
) -> dict[Any, Any]:
    update_notes: str = "Removed redundant character designer credit"

    fixed_something = False
    associated_artists_to_keep: list[Any] = []
    for artist in data["associatedArtists"]:
        if artist["linkType"] != "CharacterDesigner":
            logger.debug(f"Keeping artist {artist}")
            associated_artists_to_keep.append(artist)
        else:
            fixed_something = True

    if not fixed_something:
        logger.warning("Couldn't remove redundant character designer credit")
        return {}

    data["associatedArtists"] = associated_artists_to_keep
    data["updateNotes"] = base_update_note + update_notes
    return data

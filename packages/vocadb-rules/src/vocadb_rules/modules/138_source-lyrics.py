from typing import Any, Literal

import requests
from vdbpy.api.users import get_user_profile_by_id_1d
from vdbpy.edit.entries import edit_entry
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.types.songs import SongVersion
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Always source the lyrics."
FIELDS: list[ChangedFields] = ["Lyrics"]
ENTRY_TYPES: list[EntryType] = ["Song"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = "Partially"


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    if not isinstance(version_data, SongVersion):
        return "Wrong entry type"

    if not version_data.lyrics:
        return "Not applicable"

    for lyric in version_data.lyrics:
        if not lyric.source and not lyric.url:
            return "Rule violation"
    return "Valid"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [("Song", 852592, 2895795), ("Song", 1, 3039825)],
        "Not applicable": [("Song", 832551, 2794783), ("Song", 1, 3039820)],
        "Rule violation": [
            ("Song", 720684, 2843481),
            ("Song", 852592, 2892152),
            ("Song", 1, 3039828),
        ],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [(2895433, 31074, ("Song", 681616, 2895448))],
        "Rule violation": [(2914114, 13234, ("Song", 851857, 2914118))],
        "Not applicable": [(2921468, 27815, ("Song", 268224, 2934759))],
        "Wrong entry type": [(0, 0, ("Artist", 106476, 585128))],
    }
    return edit_check_tests, entry_check_tests


@cache_with_expiration(days=7)
def get_artist_ids_for_verified_user_7d(user_id: int) -> list[int]:
    user_profile = get_user_profile_by_id_1d(user_id)
    artist_ids: list[int] = []
    for owned_artist_data in user_profile["ownedArtistEntries"]:
        artist_ids.append(int(owned_artist_data["artist"]["id"]))

    logger.debug(f"Artist ids for user {user_id}: {artist_ids}")
    return artist_ids


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
        edit_function=add_verified_artist_as_the_lyrics_source,
        base_update_note=base_update_note,
        prompt=prompt,
        args=args,
    )


def add_verified_artist_as_the_lyrics_source(
    data: dict[Any, Any], base_update_note: str, relevant_user_id: int,
) -> dict[Any, Any]:
    if not relevant_user_id:
        logger.warning("Relevant user id required! Edit too old?")
        return {}

    update_notes: str = (
        f"Added missing lyrics sources (by verified artist"
        f" https://vocadb.net/api/users/{relevant_user_id})"
    )

    relevant_artist_ids: list[int] = [
        int(artist["artist"]["id"])
        for artist in data["artists"]
        if ("artist" in artist)
        and (
            artist["categories"] == "Producer" or artist["effectiveRoles"] == "Lyricist"
        )
    ]
    user_artist_ids = get_artist_ids_for_verified_user_7d(relevant_user_id)
    overlap = set(relevant_artist_ids) & set(user_artist_ids)
    if overlap:
        lyrics_to_keep: list[Any] = []
        """
        "isNew": false,
        "cultureCodes": ["fr"],
        "source": "test lyrics url source",
        "translationType": "Original",
        "url": "test lyrics url",
        "value": "test lyrics",
        """
        for lyrics in data["lyrics"]:
            fixed_lyrics = lyrics
            if not lyrics["source"]:
                fixed_lyrics["source"] = (
                    f"verified artist https://vocadb.net/api/users/{relevant_user_id}"
                )
            lyrics_to_keep.append(fixed_lyrics)

        logger.info(update_notes)
        data["lyrics"] = lyrics_to_keep
        data["updateNotes"] = base_update_note + update_notes

        return data
    logger.info("Couldn't find verified artists to source the lyrics")
    return {}

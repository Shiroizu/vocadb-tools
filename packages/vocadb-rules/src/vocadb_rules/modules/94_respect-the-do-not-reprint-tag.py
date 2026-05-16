from pathlib import Path
from typing import Any, Literal, cast

import requests
from vdbpy.api.entries import (
    get_entry_link,
    get_saved_entry_search,
    is_entry_tagged_1d,
)
from vdbpy.api.songs import get_cached_song_by_entry_id_and_version_id
from vdbpy.config import ARTIST_API_URL, SONG_API_URL
from vdbpy.edit.entries import edit_entry
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.types.songs import OptionalSongFieldName, SongEntry, SongVersion
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = (
    "If the main artist or the song entry is tagged "
    "with 'do not reupload', do not add any reprints."
)
FIELDS: list[ChangedFields] = ["PVs", "Artists"]
ENTRY_TYPES: list[EntryType] = ["Song"]
COMPLETE = True
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = True
TAG_ID = 1695

# TODO convert to tag follow

def find_relevant_entries(save_dir: Path) -> set[EntryTuple]:
    song_entries_to_return: set[EntryTuple] = set()
    tagged_artists = set(
        get_saved_entry_search(
            save_dir / f"artists_tagged_with_{TAG_ID}.csv",
            ARTIST_API_URL,
            {"tagId[]": TAG_ID},
        )[0],
    )
    for artist_entry in tagged_artists:
        artist_id = artist_entry[1]
        params = {
            "artistId[]": artist_id,
            "onlyWithPVs": True,
            "fields": "Artists,PVs",
        }
        songs_by_tagged_artist = get_saved_entry_search(
            save_dir / f"songs_by_{artist_id}_tagged_with_{TAG_ID}.csv",
            SONG_API_URL,
            params,
        )[0]
        song_entries_to_return.update(cast("set[EntryTuple]", songs_by_tagged_artist))

    tagged_songs = set(
        get_saved_entry_search(
            save_dir / f"songs_tagged_with_{TAG_ID}.csv",
            SONG_API_URL,
            {"tagId[]": TAG_ID},
        )[0],
    )
    song_entries_to_return.update(tagged_songs)

    return song_entries_to_return


def get_main_song_producers(entry_id: int, version_id: int) -> set[EntryTuple]:
    # TODO move to vdbpy
    main_song_producers: set[EntryTuple] = set()
    fields_to_include: set[OptionalSongFieldName] = {"artists"}
    song_entry_data: SongEntry = get_cached_song_by_entry_id_and_version_id(
        song_id=entry_id,
        version_id=version_id,
        fields=fields_to_include,
    )
    entry_link = get_entry_link("Song", entry_id)
    if song_entry_data.artists != "Unknown":
        for artist in song_entry_data.artists:
            if (
                not artist.is_support
                and artist.entry != "Custom artist"
                and "Producer" in artist.categories
            ):
                main_song_producers.add(("Artist", artist.entry.artist_id))

    if not main_song_producers:
        logger.warning(f"No main producers for {entry_link}")
    return main_song_producers


def check_entry_version_for_rule(
    version_data: BaseEntryVersion, is_relevant_entry: bool | None = None,
) -> RuleModuleResult:
    if not isinstance(version_data, SongVersion):
        return "Wrong entry type"

    is_tagged = (
        True
        if is_relevant_entry
        else is_entry_tagged_1d(("Song", version_data.entry_id), TAG_ID)
    )

    if not is_tagged:
        main_artists = get_main_song_producers(
            version_data.entry_id, version_data.version_id,
        )
        logger.debug(f"Main song artists: {main_artists}")
        version_artist_ids = {artist.artist_id for artist in version_data.artists}
        main_artist_ids = {entry[1] for entry in main_artists}
        assert version_artist_ids >= main_artist_ids, (
            f"Version artist ids: {version_artist_ids}, "
            f"main artist ids: {main_artist_ids}"
        )
        for artist_entry in main_artists:
            artist_tagged = is_entry_tagged_1d(("Artist", artist_entry[1]), TAG_ID)
            logger.debug(f"Main song artist tagged: {artist_tagged}")
            if artist_tagged:
                is_tagged = True
                break

    reprint_pvs = [
        (pv.pv_service, pv.pv_id) for pv in version_data.pvs if pv.pv_type == "Reprint"
    ]

    if is_tagged:
        if reprint_pvs:
            logger.debug("Tagged and reprints -> rule violation")
            return "Rule violation"
        logger.debug("Tagged but no reprint -> Valid")
        return "Valid"
    logger.debug("Not tagged -> Not applicable")
    return "Not applicable"


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
        edit_function=remove_reprints,
        base_update_note=base_update_note,
        prompt=prompt,
        args=args,
    )


def remove_reprints(
    data: dict[Any, Any],
    base_update_note: str = "",
    args: Any = None,
) -> dict[Any, Any]:
    update_notes: str = "Removed reprints https://vocadb.net/T/1695:"

    reprints = [pv for pv in data["pvs"] if pv["pvType"] == "Reprint"]
    if not reprints:
        logger.warning("No reprints found!")
        return {}

    data["updateNotes"] = base_update_note + update_notes
    data["pvs"] = [pv for pv in data["pvs"] if pv["pvType"] != "Reprint"]
    return data


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {}
    entry_check_tests: CorrectEntryCheckTestResult = {}
    return edit_check_tests, entry_check_tests

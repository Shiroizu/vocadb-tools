import json
import time
from collections.abc import Callable
from typing import Any

import requests

from vdbpy.types.mappings import api_urls_by_entry_type
from vdbpy.types.shared import EntryTuple, Service
from vdbpy.utils.console import get_boolean
from vdbpy.utils.logger import get_logger

logger = get_logger()


def _add_event_id_to_entry_data(
    data: dict[Any, Any],
    base_update_notes: str,  # noqa: ARG001
    id_to_add: int,
) -> dict[Any, Any]:
    entry_event_ids = [event["id"] for event in data["releaseEvents"]]
    if id_to_add in entry_event_ids:
        logger.warning("Event already added to the entry.")
        return {}
    update_notes = f"Added event {id_to_add}"
    logger.info(f"Update_notes = {update_notes}")
    data["releaseEvents"].append({"id": id_to_add})
    data["updateNotes"] = update_notes
    return data


def _add_artist_id_to_entry_data(
    data: dict[Any, Any],
    id_to_add: int,
) -> dict[Any, Any]:
    artists_to_keep: list[Any] = []
    for artist in data["artists"]:
        if "artist" in artist and artist["artist"]["id"] == id_to_add:
            logger.warning(f"Artist {id_to_add} already added.")
            return {}
        artists_to_keep.append(artist)

    artists_to_keep.append({"artist": {"id": id_to_add}})
    update_notes = f"Added arist {id_to_add}"
    logger.debug(f"Update_notes = {update_notes}")
    data["updateNotes"] = update_notes
    data["artists"] = artists_to_keep
    return data


def _remove_artist_id_from_entry_data(
    data: dict[Any, Any],
    id_to_remove: int,
) -> dict[Any, Any]:
    artists_to_keep: list[Any] = []
    artist_found = False
    for artist in data["artists"]:
        if "artist" in artist and artist["artist"]["id"] == id_to_remove:
            artist_found = True
            continue
        artists_to_keep.append(artist)

    if not artist_found:
        logger.warning(f"Artist {id_to_remove} was not found.")
        return {}

    update_notes = f"Removed artist {id_to_remove}"
    logger.debug(f"Update_notes = {update_notes}")
    data["updateNotes"] = update_notes
    data["artists"] = artists_to_keep
    return data


def _replace_artist_in_entry_data(
    data: dict[Any, Any],
    base_update_note: str,  # noqa: ARG001
    artist_ids: tuple[int, int],
) -> dict[Any, Any]:
    id_to_remove, id_to_add = artist_ids
    removed_data = _remove_artist_id_from_entry_data(data, id_to_remove)
    removed_notes = removed_data.get("updateNotes")
    if removed_notes:
        data = removed_data
    added_data = _add_artist_id_to_entry_data(data, id_to_add)
    if added_data:
        if removed_notes:
            update_notes = f"Replaced artist {id_to_remove} with {id_to_add}."
            logger.info(f"update_notes = {update_notes}")
            added_data["updateNotes"] = update_notes
        return added_data
    if removed_notes:
        return removed_data
    return {}


def _mark_pvs_unavailable_in_entry_data(
    data: dict[Any, Any],
    base_update_note: str,  # noqa: ARG001
    service: Service | None,
) -> dict[Any, Any]:
    logger.info("Marking all original PVs unavailable.")
    if service:
        logger.info(f"Restricting to PV service {service}")

    pvs_to_keep: list[Any] = []
    update_notes: str = ""
    for pv in data["pvs"]:
        logger.debug(f"{pv['pvId']} {pv['service']} ({pv['pvType']})")
        if pv["pvType"] == "Original" and not pv["disabled"]:
            if service:
                if pv["service"] == service:
                    update_notes += f"Marked {pv['url']} as unavailable, "
                    pv["disabled"] = True
            else:
                update_notes += f"Marked {pv['url']} as unavailable, "
                pv["disabled"] = True
        pvs_to_keep.append(pv)

    if not update_notes:
        logger.info("Found no PVs to update.")
        return {}

    data["updateNotes"] = update_notes
    data["pvs"] = pvs_to_keep
    return data


# --------------------------------------------- #


def trim_update_notes(update_notes: str, max_length: int = 200) -> str:
    if len(update_notes) > max_length:
        update_notes = update_notes[: max_length - 1] + "…"
        logger.warning(f"Trimmed update notes below {max_length} characters:")
        logger.warning(update_notes)
    return update_notes


def edit_entry(
    session: requests.Session,
    entry: EntryTuple,
    edit_function: Callable[[dict[Any, Any], str, Any], dict[Any, Any]],
    base_update_note: str = "",
    prompt: bool = True,
    args: Any = None,  # noqa: ANN401
) -> bool:
    entry_type, entry_id = entry
    api_url = f"{api_urls_by_entry_type[entry_type]}/{entry_id}"
    entry_data = session.get(f"{api_url}/for-edit").json()
    logger.debug(f"{entry_data=}")
    fixed_data = edit_function(entry_data, base_update_note, args)
    if not fixed_data:
        logger.warning("Nothing to fix")
        return False
    fixed_data["updateNotes"] = trim_update_notes(fixed_data["updateNotes"])
    logger.info(f"Update notes: {fixed_data['updateNotes']}")
    assert fixed_data["updateNotes"]  # noqa: S101
    logger.debug(f"{fixed_data=}")
    if prompt and not get_boolean("Fix entry?"):
        return False
    logger.info(f"Posting to {api_url}")
    request_save = session.post(api_url, {"contract": json.dumps(fixed_data)})
    request_save.raise_for_status()

    # TODO post_json function
    # from requests.adapters import HTTPAdapter, Retry
    # retries = Retry(total=5, backoff_factor=1, status_forcelist=[ ? ])
    # session.mount('http://', HTTPAdapter(max_retries=retries))

    time.sleep(1)
    return True


def replace_artist_in_entry(
    session: requests.Session,
    entry: EntryTuple,
    id_to_remove: int,
    id_to_add: int,
    prompt: bool = True,
) -> bool:
    return edit_entry(
        session=session,
        entry=entry,
        edit_function=_replace_artist_in_entry_data,
        args=(id_to_remove, id_to_add),
        prompt=prompt,
    )


def mark_pvs_unavailable_for_entry(
    session: requests.Session,
    entry: EntryTuple,
    service: Service | None = None,
    prompt: bool = True,
) -> bool:
    # Does not do an extra check if the PV is unavailable or not!
    return edit_entry(
        session=session,
        entry=entry,
        edit_function=_mark_pvs_unavailable_in_entry_data,
        args=service,
        prompt=prompt,
    )


def add_event_to_entry(
    session: requests.Session,
    entry: EntryTuple,
    event_id: int,
    prompt: bool = True,
) -> bool:
    return edit_entry(
        session=session,
        entry=entry,
        edit_function=_add_event_id_to_entry_data,
        args=event_id,
        prompt=prompt,
    )

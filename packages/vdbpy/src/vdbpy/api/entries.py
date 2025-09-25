import random
from typing import get_args

from vdbpy.config import WEBSITE
from vdbpy.types import Edit_type, Entry_type, UserEdit
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount, fetch_json

logger = get_logger()

edit_event_map: dict[str, Edit_type] = {
    "PropertiesUpdated": "Updated",
    "Deleted": "Deleted",
    "Created": "Created",
}


def parse_edits_from_archived_versions(
    data: list[dict], entry_type: Entry_type, entry_id: int
) -> list[UserEdit]:
    parsed_edits: list[UserEdit] = []
    for edit_object in data:
        parsed_edits.append(
            UserEdit(
                user_id=edit_object["author"]["id"],
                edit_date=edit_object["created"],
                entry_type=entry_type,
                entry_id=entry_id,
                version_id=edit_object["id"],
                edit_event=edit_event_map[edit_object["reason"]],
                changed_fields=edit_object["changedFields"],
                update_notes=edit_object["notes"],
            )
        )
    return parsed_edits

@cache_with_expiration(days=1)
def get_entry_versions(entry_type: Entry_type, entry_id: int) -> list[UserEdit]:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/versions"
    data = fetch_json(url)["archivedVersions"]
    return parse_edits_from_archived_versions(data, entry_type, entry_id)

@cache_without_expiration()
def get_entry_version(entry_type: Entry_type, version_id: int) -> dict:
    # TODO proper return types: Song | Album | ..
    url = f"{WEBSITE}/api/{add_s(entry_type)}/versions/{version_id}"
    return fetch_json(url)["versions"]["firstData"]


@cache_with_expiration(days=1)
def get_cached_entry_count_by_entry_type(entry_type: str):
    url = f"{WEBSITE}/api/{add_s(entry_type)}?getTotalCount=True&maxResults=1"
    return fetch_cached_totalcount(url)


def get_random_entry():
    entry_type = random.choice(get_args(Entry_type))
    logger.info(f"Chose entry type '{entry_type}'")
    entry_type = add_s(entry_type)
    total = get_cached_entry_count_by_entry_type(entry_type)
    random_index = random.randint(1, total)
    url = f"{WEBSITE}/api/{entry_type}"
    params = {"getTotalCount": True, "maxResults": 1, "start": random_index}
    return fetch_json(url, params=params)["items"][0]


def is_deleted(entry_type: Entry_type, entry_id: int) -> bool:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}"
    entry = fetch_json(url)
    if "deleted" in entry:
        return entry["deleted"]
    return False


def delete_entry(
    session,
    entry_type: Entry_type,
    entry_id: int,
    force=False,
    deletion_msg="",
    prompt=True,
) -> bool:
    if is_deleted(entry_type, entry_id):
        logger.warning(f"Entry {entry_id} has already been deleted.")
        return False

    assert entry_type in get_args(Entry_type), "Invalid entry type"  # noqa: S101
    logger.warning(f"Deleting {entry_type} entry {entry_id}...")
    if prompt:
        _ = input("Press enter to delete...")

    if not force:
        # TODO comply with content removal guidelines
        logger.warning("Careful entry deletion has not been implemented.")
        return False
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}"
    if deletion_msg:
        url += f"?notes={deletion_msg}"

    deletion_attempt = session.delete(url)
    deletion_attempt.raise_for_status()

    return True

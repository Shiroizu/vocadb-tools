import random
from typing import get_args

from vdbpy.config import WEBSITE
from vdbpy.types import Entry_type
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount, fetch_json

logger = get_logger()


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


def delete_entry(
    session,
    selected_entry_type: Entry_type,
    entry_id: int,
    force=False,
    deletion_msg="",
):
    # DUPE deletions are currently possible (harmless)
    # https://beta.vocadb.net/Artist/Versions/151812
    # TODO fix ^

    assert selected_entry_type in get_args(Entry_type), "Invalid entry type"  # noqa: S101
    logger.warning(f"Deleting {selected_entry_type} entry {entry_id}...")

    if not force:
        # TODO comply with content removal guidelines
        logger.warning("Careful entry deletion has not been implemented.")
        return
    url = f"{WEBSITE}/api/{add_s(selected_entry_type)}/{entry_id}"
    if deletion_msg:
        url += f"?notes={deletion_msg}"

    deletion_attempt = session.delete(url)
    deletion_attempt.raise_for_status()

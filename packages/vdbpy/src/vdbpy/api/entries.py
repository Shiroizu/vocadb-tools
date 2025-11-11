import random
from pathlib import Path
from typing import Any, get_args

import requests

from vdbpy.api.users import get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.parsers.albums import parse_album_version
from vdbpy.parsers.artists import parse_artist_version
from vdbpy.parsers.events import parse_release_event_version
from vdbpy.parsers.series import (
    parse_release_event_series_version,
)
from vdbpy.parsers.songs import parse_song_version
from vdbpy.parsers.tags import parse_tag_version
from vdbpy.parsers.venus import parse_venue_version
from vdbpy.types.albums import AlbumVersion
from vdbpy.types.artists import ArtistVersion
from vdbpy.types.events import ReleaseEventVersion
from vdbpy.types.series import ReleaseEventSeriesVersion
from vdbpy.types.shared import (
    EditType,
    EntryTuple,
    EntryType,
)
from vdbpy.types.songs import SongVersion
from vdbpy.types.tags import TagVersion
from vdbpy.types.venues import VenueVersion
from vdbpy.utils.cache import cache_without_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.files import get_lines, save_file
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_cached_total_count,
    fetch_json,
    fetch_json_items_with_total_count,
)

logger = get_logger()

edit_event_map: dict[str, EditType] = {
    "PropertiesUpdated": "Updated",
    "Updated": "Updated",
    "Reverted": "Reverted",
    "Merged": "Updated",
    "Deleted": "Deleted",
    "Created": "Created",
}

entry_type_to_url: dict[EntryType, str] = {
    "Song": "S",
    "Artist": "Ar",
    "Album": "Al",
    "Venue": "Venue/Details",
    "Tag": "T",
    "ReleaseEvent": "E",
    "ReleaseEventSeries": "Es",
    "SongList": "L",
}

entry_url_to_type: dict[str, EntryType] = {v: k for k, v in entry_type_to_url.items()}
type EntryDetails = dict[Any, Any]  # TODO implement


def get_entry_details(entry_type: EntryType, entry_id: int) -> EntryDetails:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/details"
    return fetch_json(url)


def get_entry_tag_ids(entry_type: EntryType, entry_id: int) -> list[int]:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/"
    params = {"fields": "Tags"}
    tags = fetch_json(url, params=params)["tags"]
    return [int(tag["tag"]["id"]) for tag in tags]


def is_entry_deleted(entry_type: EntryType, entry_id: int) -> bool:
    entry_details = get_entry_details(entry_type, entry_id)
    if "deleted" in entry_details:
        return entry_details["deleted"]
    return False


@cache_without_expiration()
def cached_is_entry_deleted(entry_type: EntryType, entry_id: int) -> bool:
    return is_entry_deleted(entry_type, entry_id)


@cache_without_expiration()
def get_cached_raw_entry_version(
    entry_type: EntryType, version_id: int
) -> dict[Any, Any]:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/versions/{version_id}"
    return fetch_json(url)


def get_cached_entry_version(  # noqa: PLR0911
    entry_type: EntryType, version_id: int
) -> (
    AlbumVersion
    | ArtistVersion
    | SongVersion
    | TagVersion
    | ReleaseEventVersion
    | ReleaseEventSeriesVersion
    | VenueVersion
    | None
):
    try:
        data = get_cached_raw_entry_version(entry_type, version_id)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:  # noqa: PLR2004
            logger.warning(f"Version data not available for v{version_id}")
        return None
    match entry_type:
        case "Album":
            return parse_album_version(data)
        case "Artist":
            return parse_artist_version(data)
        case "Song":
            return parse_song_version(data)
        case "Tag":
            return parse_tag_version(data)
        case "ReleaseEvent":
            return parse_release_event_version(data)
        case "ReleaseEventSeries":
            return parse_release_event_series_version(data)
        case "Venue":
            return parse_venue_version(data)
        case _:
            msg = f"Unknown entry type {entry_type}"
            raise ValueError(msg)


# TODO get entry


def get_cached_entry_count_by_entry_type(entry_type: EntryType) -> int:
    url = f"{WEBSITE}/api/{add_s(entry_type)}"
    return fetch_cached_total_count(url)


def get_random_entry(
    entry_type: EntryType | None = None,
) -> dict[Any, Any]:  # TODO type
    selected_entry_type: EntryType = (
        entry_type if entry_type else random.choice(get_args(EntryType))
    )
    total = get_cached_entry_count_by_entry_type(selected_entry_type)
    random_index = random.randint(1, total)
    url = f"{WEBSITE}/api/{add_s(str(entry_type))}"
    params = {"getTotalCount": True, "maxResults": 1, "start": random_index}
    return fetch_json(url, params=params)["items"][0]


def delete_entry(
    session: requests.Session,
    entry_type: EntryType,
    entry_id: int,
    force: bool = False,
    deletion_msg: str = "",
    prompt: bool = True,
) -> bool:
    if is_entry_deleted(entry_type, entry_id):
        logger.warning(f"Entry {entry_id} has already been deleted.")
        return False

    assert entry_type in get_args(EntryType), "Invalid entry type"  # noqa: S101
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


def get_versions_url(entry_type: EntryType, entry_id: int) -> str:
    # TODO fix
    return f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/versions"


def get_entry_link(entry_type: EntryType, entry_id: int) -> str:
    if entry_type == "User":
        username = get_username_by_id(entry_id)
        return f"{WEBSITE}/Profile/{username}"
    return f"{WEBSITE}/{entry_type_to_url[entry_type]}/{entry_id}"


def get_entry_from_link(entry_link: str) -> EntryTuple:
    # https://vocadb.net/S/83619
    # --> ("Song", 83619)
    link = entry_link.split(WEBSITE + "/")[1]
    if "venue" in link.lower():
        entry_id = int(link.split("/")[2])
        return ("Venue", entry_id)

    entry_type_slug, entry_id_str, *_ = link.split("/")
    entry_type = entry_url_to_type[entry_type_slug]
    return (entry_type, int(entry_id_str))


def is_entry_tagged(entry: EntryTuple, tag_id: int) -> bool:
    return tag_id in get_entry_tag_ids(*entry)


def read_entries_from_file(file: Path) -> set[EntryTuple]:
    entries: set[EntryTuple] = set()
    for line in get_lines(file):
        if not line.strip():
            continue
        entry_type, entry_id = line.split(",")
        if entry_type not in get_args(EntryType):
            msg = f"Malformatted entry type {entry_type} in {file}"
            raise ValueError(msg)
        entries.add((entry_type, int(entry_id)))  # type: ignore
    return entries


def write_entries_to_file(
    file: Path, entries: set[EntryTuple], delimiter: str = ","
) -> None:
    # TODO convert exising files to this
    lines_to_write = [
        delimiter.join((entry_type, str(entry_id))) for entry_type, entry_id in entries
    ]
    save_file(file, lines_to_write)


def get_saved_entry_search(
    file: Path,
    entry_type: EntryType,
    search_url: str,
    params: dict[Any, Any] | None = None,
    recheck_mode: int = 2,
) -> set[EntryTuple]:
    # Possible modes
    # 1) if count changed, recheck and stop when already seen entry found
    # 2) if count changed, recheck all (current)
    # 3) always recheck even if previous count hasn't changed
    # TODO implement 1 & 3

    if recheck_mode != 2:  # noqa: PLR2004
        raise NotImplementedError

    previous_entries = read_entries_from_file(file)
    _, total_count = fetch_json_items_with_total_count(
        search_url, params=params, max_results=1
    )
    if len(previous_entries) == total_count:
        logger.debug(
            f"The number of entries to check has not changed ({len(previous_entries)})."
        )
        return previous_entries

    logger.info("The number of entries to check has changed: ")
    logger.info(f"({len(previous_entries)} -> {total_count}")

    entries, _ = fetch_json_items_with_total_count(search_url, params=params)

    # TODO detect entry type instead of passing it
    entry_set: set[EntryTuple] = {(entry_type, int(entry["id"])) for entry in entries}
    write_entries_to_file(file, entry_set)

    return entry_set


"""
@dataclass
class BaseEntry:
    id: int
    name: str
    create_date: datetime
    default_name: str
    default_name_language: DefaultLanguages
    version: int
    status: EntryStatus


@dataclass
class Song(BaseEntry):
    artist_string: str
    favorite_count: int
    length_seconds: int
    original_version_id: int
    publish_date: datetime
    pv_services: list[Service]
    rating_score: int
    song_type: SongType"""

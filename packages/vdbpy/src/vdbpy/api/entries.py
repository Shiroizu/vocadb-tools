import random
from pathlib import Path
from typing import Any, get_args

import requests

from vdbpy.api.users import get_username_by_id
from vdbpy.config import (
    ALBUM_API_URL,
    ARTIST_API_URL,
    EVENT_API_URL,
    SERIES_API_URL,
    SONG_API_URL,
    TAG_API_URL,
    VENUE_API_URL,
    WEBSITE,
)
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
    fetch_json_items,
    fetch_total_count,
)

logger = get_logger()

edit_event_map: dict[str, EditType] = {
    "Created": "Created",
    "Updated": "Updated",
    "PropertiesUpdated": "Updated",
    "Reverted": "Reverted",
    "Deleted": "Deleted",
    "Merged": "Updated",
    "Restored": "Restored",
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


api_urls_by_entry_type: dict[EntryType, str] = {
    "Song": SONG_API_URL,
    "Album": ALBUM_API_URL,
    "Artist": ARTIST_API_URL,
    "Tag": TAG_API_URL,
    "ReleaseEvent": EVENT_API_URL,
    "ReleaseEventSeries": SERIES_API_URL,
    "Venue": VENUE_API_URL,
}
entry_types_by_api_url: dict[str, EntryType] = {
    v: k for k, v in api_urls_by_entry_type.items()
}


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


def read_entries_from_file(file: Path) -> list[EntryTuple]:
    entries: list[EntryTuple] = []
    for line in get_lines(file):
        if not line.strip():
            continue
        entry_type, entry_id = line.split(",")
        if entry_type not in get_args(EntryType):
            msg = f"Malformatted entry type {entry_type} in {file}"
            raise ValueError(msg)
        if (entry_type, int(entry_id)) in entries:
            logger.warning(f"Duplicate entry {entry_type} {entry_id} in {file}")
            continue
        entries.append((entry_type, int(entry_id)))  # type: ignore
    return entries


def write_entries_to_file(
    file: Path, entries: list[EntryTuple], delimiter: str = ","
) -> None:
    lines_to_write = [
        delimiter.join((entry_type, str(entry_id))) for entry_type, entry_id in entries
    ]
    logger.debug(f"Saving {len(lines_to_write)} entries")
    logger.debug(f"from {lines_to_write[0]} to {lines_to_write[-1]}")
    save_file(file, lines_to_write)


def get_saved_entry_search(
    file: Path,
    search_url: str,
    params: dict[Any, Any] | None = None,
    lazy_recheck: bool = True,
) -> tuple[list[EntryTuple], tuple[int, int]]:
    logger.debug(f"Fetching saved entry search with file '{file}'")

    if params and "sort" not in params:
        params["sort"] = "AdditionDate"

    logger.debug(f"url {search_url} and params {params}")
    entry_type = entry_types_by_api_url[search_url]

    previous_entries = read_entries_from_file(file)
    logger.debug(f"Found {len(previous_entries)} previous entries")
    most_recent_entry_id: int = 0
    if previous_entries:
        most_recent_entry_id = previous_entries[0][1]
        logger.info(f"Most recent entry is {most_recent_entry_id}")

    total_count = fetch_total_count(search_url, params=params)
    if len(previous_entries) == total_count:
        logger.debug(
            f"The number of entries to check has not changed ({len(previous_entries)})."
        )
        return previous_entries, (total_count, 0)

    logger.info("The number of entries to check has changed: ")
    logger.info(f"({len(previous_entries)} -> {total_count}")

    if lazy_recheck and most_recent_entry_id:

        def limit_function(item: dict[Any, Any]) -> bool:
            return item["id"] == most_recent_entry_id

        limit = limit_function if lazy_recheck else None
        new_entries_json = fetch_json_items(search_url, params=params, limit=limit)
        new_entries: list[EntryTuple] = []
        entry_type = entry_types_by_api_url[search_url]
        for entry in new_entries_json:
            if (entry_type, entry["id"]) not in new_entries:
                new_entries.append((entry_type, entry["id"]))

        logger.debug(f"{len(new_entries)} + {len(previous_entries)} =? {total_count}")
        if len(new_entries) + len(previous_entries) == total_count:
            logger.info(
                "The number of new entries + previous entries matches the total count."
            )
            combined_entries = new_entries + previous_entries
            if len(combined_entries) == len(set(combined_entries)):
                logger.debug("Saving combined entries")
                write_entries_to_file(file, combined_entries)
                return combined_entries, (
                    len(previous_entries),
                    len(new_entries_json),
                )
            logger.warning("Combined entries includes duplicates.")
        logger.warning("Couldn't lazy recheck entries")
    entries_json = fetch_json_items(search_url, params=params)

    entries: list[EntryTuple] = []
    for entry in entries_json:
        if (entry_type, entry["id"]) not in entries:
            entries.append((entry_type, entry["id"]))

    logger.debug("Saving fully checked entries")
    write_entries_to_file(file, entries)

    return entries, (len(previous_entries), len(entries))


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

import random
from typing import (
    get_args,
)

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
from vdbpy.types.core import EditType, Entry, EntryType
from vdbpy.types.entry_versions import (
    AlbumVersion,
    ArtistVersion,
    ReleaseEventSeriesVersion,
    ReleaseEventVersion,
    SongVersion,
    TagVersion,
    VenueVersion,
)
from vdbpy.utils.cache import cache_without_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount, fetch_json

logger = get_logger()

edit_event_map: dict[str, EditType] = {
    "PropertiesUpdated": "Updated",
    "Updated": "Updated",
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
type EntryDetails = dict  # TODO


def get_entry_details(entry_type: EntryType, entry_id: int) -> EntryDetails:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/details"
    return fetch_json(url)


def is_entry_deleted(entry_type: EntryType, entry_id: int) -> bool:
    entry_details = get_entry_details(entry_type, entry_id)
    if "deleted" in entry_details:
        return entry_details["deleted"]
    return False


@cache_without_expiration()
def cached_is_entry_deleted(entry_type: EntryType, entry_id: int) -> bool:
    return is_entry_deleted(entry_type, entry_id)


@cache_without_expiration()
def get_cached_raw_entry_version(entry_type: EntryType, version_id: int) -> dict:
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
):
    data = get_cached_raw_entry_version(entry_type, version_id)
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
            raise Exception(f"Unknown entry type {entry_type}")
    return data["versions"]["firstData"]


def get_cached_entry_count_by_entry_type(entry_type: str) -> int:
    url = f"{WEBSITE}/api/{add_s(entry_type)}?getTotalCount=True&maxResults=1"
    return fetch_cached_totalcount(url)


def get_random_entry() -> dict:  # TODO
    entry_type = random.choice(get_args(EntryType))
    logger.info(f"Chose entry type '{entry_type}'")
    entry_type = add_s(entry_type)
    total = get_cached_entry_count_by_entry_type(entry_type)
    random_index = random.randint(1, total)
    url = f"{WEBSITE}/api/{entry_type}"
    params = {"getTotalCount": True, "maxResults": 1, "start": random_index}
    return fetch_json(url, params=params)["items"][0]


def delete_entry(
    session,
    entry_type: EntryType,
    entry_id: int,
    force=False,
    deletion_msg="",
    prompt=True,
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


def get_entry_from_link(entry_link: str) -> Entry:
    # https://vocadb.net/S/83619
    # --> ("Song", 83619)
    link = entry_link.split(WEBSITE + "/")[1]
    if "venue" in link.lower():
        entry_id = int(link.split("/")[2])
        return ("Venue", entry_id)

    entry_type_slug, entry_id_str, *_ = link.split("/")
    entry_type = entry_url_to_type[entry_type_slug]
    return (entry_type, int(entry_id_str))

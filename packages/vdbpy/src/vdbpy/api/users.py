from datetime import UTC, datetime
from typing import Any, get_args

from vdbpy.config import ACTIVITY_API_URL, USER_API_URL, WEBSITE
from vdbpy.types.shared import EditType, EntryType
from vdbpy.types.users import User, UserGroup
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.data import get_monthly_count
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
    fetch_totalcount,
)

logger = get_logger()


def get_users(params: dict[Any, Any] | None) -> list[User]:
    return fetch_json_items(USER_API_URL, params=params)


def get_users_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[User], int]:
    return fetch_json_items_with_total_count(
        USER_API_URL, params=params, max_results=max_results
    )


def get_user(params: dict[Any, Any] | None) -> User:
    result = fetch_json(USER_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_50_most_recent_users() -> list[User]:
    # Inverse sorting not supported for RegisterDate
    # 1) Get total count
    # 2) Query with start = total count - 50
    params: dict[Any, Any] = {"includeDisabled": True}
    total_count = fetch_totalcount(USER_API_URL, params=params)
    params["start"] = total_count - 50
    params["sort"] = "RegisterDate"
    params["maxResults"] = 50
    return fetch_json(USER_API_URL, params=params)["items"][::-1]


def get_username_by_id(user_id: int, include_usergroup: bool = False) -> str:
    user_api_url = f"{USER_API_URL}/{user_id}"
    data = fetch_json(user_api_url)
    if include_usergroup:
        return f"{data['name']} ({data['groupId']})"
    return data["name"]


@cache_without_expiration()
def get_cached_username_by_id(user_id: int, include_usergroup: bool = False) -> str:
    return get_username_by_id(user_id, include_usergroup)


@cache_with_expiration(days=1)
def get_user_profile_by_username_1d(username: str) -> dict[Any, Any]:  # TODO type
    """Get user profile data.

    # -- Mod cred data --
    "additionalPermissions": [],
    "effectivePermissions": [,
    "email": "",
    "lastLogin": "2025-01-21T02:08:00.363",
    "lastLoginAddress": "",
    "oldUsernames": [],

    # -- Rest of the data --
    "aboutMe": "",
    "active": true,
    "albumCollectionCount": 0,
    "anonymousActivity": false,
    "artistCount": 0,
    "commentCount": 0,
    "createDate": "2012-10-30T09:33:28",
    "customTitle": "",
    "designatedStaff": true,
    "editCount": 0,
    "emailVerified": true,
    "favoriteAlbums": [],
    "favoriteSongCount": 0,
    "favoriteTags": [],
    "followedArtists": [],
    "groupId": "Admin",
    "id": 0,
    "isVeteran": true,
    "knownLanguages": [],
    "latestComments": [],
    "latestRatedSongs": [],
    "level": 0,
    "location": "",
    "mainPicture": {},
    "name": "Name",
    "ownedArtistEntries": [],
    "possibleProducerAccount": false,
    "power": 0,
    "publicAlbumCollection": false,
    "standalone": false,
    "submitCount": 0,
    "supporter": false,
    "tagVotes": 0,
    "twitterName": "",
    "verifiedArtist": false,
    "webLinks": []
    }
    """
    api_url = f"{WEBSITE}/api/profiles/{username}"
    return fetch_json(api_url)


def get_user_profile_by_id(user_id: int) -> dict[Any, Any]:  # TODO type
    username = get_username_by_id(user_id)
    return get_user_profile_by_username_1d(username)


@cache_with_expiration(days=1)
def find_user_by_username_and_mode_1d(username: str, mode: str) -> tuple[str, int]:
    # Available values : Auto, Partial, StartsWith, Exact, Words

    valid_search_modes = ["auto", "partial", "startswith", "exact", "words"]
    if mode.lower() not in valid_search_modes:
        logger.warning(f"Invalid search mode '{mode.lower()}'.")
        logger.warning(
            f"Search mode must be within valid search modes: {valid_search_modes}."
        )
        return ("", 0)

    params = {
        "query": username,
        "maxResults": 1,
        "nameMatchMode": mode,
        "includeDisabled": True,
    }
    data = fetch_json(USER_API_URL, params=params)
    if data and data["items"]:
        username = data["items"][0]["name"]
        user_id = data["items"][0]["id"]
        return (username, user_id)

    logger.info(f"User id not found with username '{username}' and mode '{mode}'")
    return ("", 0)


@cache_with_expiration(days=1)
def find_user_by_username_1d(username: str) -> tuple[str, int]:
    # Available values : Auto, Partial, StartsWith, Exact, Words

    exact_match = find_user_by_username_and_mode_1d(username, "Exact")
    if exact_match[1]:
        return exact_match

    return find_user_by_username_and_mode_1d(username, "Partial")


@cache_without_expiration()
def find_cached_user_by_username(username: str) -> tuple[str, int]:
    return find_user_by_username_1d(username)


@cache_with_expiration(days=1)
def get_entry_matrix_by_user_id_1d(
    user_id: int, since: str = "", before: str = ""
) -> dict[EntryType, dict[EditType, int]]:
    # 1) Check the total counts of the most common entryType/editEvent combinations:
    # 2) Stop when total count reached to reduce the number of API calls
    #
    # Other entry types that are not listed here return 0
    # Related github issue: https://github.com/VocaDB/vocadb/issues/1766
    #
    # The API docs include three additional entryTypes: PV, DiscussionTopic, User
    # but these do not return anything

    entry_matrix: dict[EntryType, dict[EditType, int]] = {
        entry_type: dict.fromkeys(get_args(EditType), 0)
        for entry_type in get_args(EntryType)
    }

    params: dict[Any, Any] = {"maxResults": 1, "getTotalCount": True, "userId": user_id}

    if since:
        params["since"] = since

    if before:
        params["before"] = before

    total_count = fetch_json(ACTIVITY_API_URL, params=params)["totalCount"]
    logger.info(f"Total edits: {total_count}")

    combinations: list[tuple[EditType, EntryType]] = [  # Sorted by how common they are
        ("Updated", "Song"),
        ("Created", "Song"),
        ("Updated", "Artist"),
        ("Created", "Artist"),
        ("Updated", "Album"),
        ("Created", "Album"),
        ("Updated", "Tag"),
        ("Updated", "ReleaseEvent"),
        ("Created", "ReleaseEvent"),
        ("Created", "Tag"),
        ("Updated", "SongList"),
        ("Deleted", "Song"),
        ("Deleted", "Artist"),
        ("Created", "SongList"),
        ("Created", "Venue"),
        ("Updated", "Venue"),
    ]

    count = 0
    for edit_type, entry_type in combinations:
        if not total_count:
            break
        params["entryType"] = entry_type
        params["editEvent"] = edit_type
        count = 0
        count = fetch_json(ACTIVITY_API_URL, params=params)["totalCount"]
        if count > 0:
            entry_matrix[entry_type][edit_type] = count
            log_line = f"{entry_type}, {edit_type}: Total count is now "
            log_line += f"{total_count} - {count} = {total_count - count}"
            logger.info(log_line)
            total_count -= count
        logger.info((edit_type, entry_type, count))

    logger.info(entry_matrix)
    if total_count != 0:
        logger.info(f"Count mismatch {total_count}, possible new activity after")
    return entry_matrix


def get_monthly_user_count(year: int, month: int) -> int:
    return get_monthly_count(year, month, USER_API_URL, param_name="joinDateBefore")


def get_user_account_age_by_user_id(user_id: int) -> int:
    """Get user account age in days."""
    username = get_username_by_id(user_id)
    creation_date = parse_date(get_user_profile_by_username_1d(username)["createDate"])
    today = datetime.now(UTC)
    return (today - creation_date).days


def get_user_group_by_user_id(user_id: int) -> UserGroup:
    return fetch_json(f"{USER_API_URL}/{user_id}")["groupId"]

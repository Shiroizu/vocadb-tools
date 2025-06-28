from typing import get_args

import requests

from vdbpy.config import WEBSITE
from vdbpy.types import Edit_type, Entry_type
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.data import split_list
from vdbpy.utils.date import get_month_strings, month_is_over
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    cache_without_expiration,
    fetch_cached_totalcount,
    fetch_json,
    fetch_json_items,
    fetch_totalcount,
)

logger = get_logger()


@cache_with_expiration(days=7)
def get_username_by_id(user_id: int, include_usergroup=False) -> str:
    user_api_url = f"{WEBSITE}/api/users/{user_id}"
    data = fetch_json(user_api_url)
    if include_usergroup:
        return f"{data['name']} ({data['groupId']})"
    return data["name"]


@cache_with_expiration(days=7)
def find_user_by_username_and_mode(username: str, mode: str) -> tuple[str, int]:
    # Available values : Auto, Partial, StartsWith, Exact, Words

    valid_search_modes = ["auto", "partial", "startswith", "exact", "words"]
    if mode.lower() not in valid_search_modes:
        logger.warning(f"Invalid search mode '{mode.lower()}'.")
        logger.warning(
            f"Search mode must be within valid search modes: {valid_search_modes}."
        )
        return ("", 0)

    user_api_url = f"{WEBSITE}/api/users/"
    params = {
        "query": username,
        "maxResults": 1,
        "nameMatchMode": mode,
        "includeDisabled": True,
    }
    data = fetch_json(user_api_url, params=params)
    if data and data["items"]:
        username = data["items"][0]["name"]
        user_id = data["items"][0]["id"]
        return (username, user_id)

    print(f"User id not found with username '{username}' and mode '{mode}'")
    return ("", 0)


@cache_with_expiration(days=7)
def find_user_by_username(username: str) -> tuple[str, int]:
    # Available values : Auto, Partial, StartsWith, Exact, Words

    exact_match = find_user_by_username_and_mode(username, "Exact")
    if exact_match[1]:
        return exact_match

    return find_user_by_username_and_mode(username, "Partial")


@cache_with_expiration(days=7)
def get_rated_songs(user_id: int, extra_params=None):
    logger.info(f"Fetching rated songs for user id {user_id}")
    api_url = f"{WEBSITE}/api/users/{user_id}/ratedSongs"
    rated_songs = fetch_json_items(api_url, extra_params)
    logger.info(f"Found total of {len(rated_songs)} rated songs.")
    return rated_songs


@cache_with_expiration(days=7)
def get_albums_by_user(user_id: int, extra_params=None):
    logger.info(f"Fetching albums for user id {user_id}")
    api_url = f"{WEBSITE}/api/users/{user_id}/albums"
    albums = fetch_json_items(api_url, extra_params)
    logger.info(f"Found total of {len(albums)} albums.")
    return albums


@cache_with_expiration(days=7)
def get_followed_artists(user_id: int, extra_params=None):
    logger.info(f"Fetching followed artists for user id {user_id}")
    api_url = f"{WEBSITE}/api/users/{user_id}/followedArtists"
    followed_artists = fetch_json_items(api_url, extra_params)
    if followed_artists:
        followed_artists = [ar["artist"] for ar in followed_artists]
    logger.info(f"Found total of {len(followed_artists)} followed artists")
    return followed_artists


@cache_with_expiration(days=1000)
def get_user_count(before_date: str):
    api_url = f"{WEBSITE}/api/users"
    params = {"joinDateBefore": before_date}
    return fetch_totalcount(api_url, params=params)


def delete_notifications(
    session: requests.Session, user_id: int, notification_ids: list[str]
):
    logger.info(f"Got total of {len(notification_ids)} notifications to delete.")
    for sublist in split_list(notification_ids):
        # https://vocadb.net/api/users/329/messages?messageId=1947289&messageId=1946744&messageId=
        deletion_url = f"{WEBSITE}/api/users/{user_id}/messages?"
        query = [f"messageId={notif_id}" for notif_id in sublist]
        deletion_url += "&".join(query)
        _ = input(f"Press enter to delete {len(sublist)} notifications")
        deletion_request = session.delete(deletion_url)
        deletion_request.raise_for_status()


def get_created_entries(username: str) -> list:
    # Also includes deleted entries
    username, user_id = find_user_by_username(username)
    max_results = 500  # TODO verify
    params = {
        "userId": user_id,
        "fields": "Entry",
        "getTotalCount": True,
        "maxResults": max_results,
        "editEvent": "Created",
    }

    logger.debug(f"Fetching created entries by user '{username}' ({user_id})")
    url = f"{WEBSITE}/api/activityEntries"
    result = fetch_json(url, params=params)
    if not result["items"]:
        logger.warning("No entries found!")
        return []
    if result["totalCount"] > max_results:
        # TODO implement using before param
        logger.warning(f"User has more than {max_results} entries! Update the script!")
        _ = input("Press enter to continue...")
    return result["items"]


@cache_with_expiration(days=1)
def get_entry_matrix(user_id: int, since="", before=""):
    # 1) Check the total counts of the most common entryType/editEvent combinations:
    # 2) Stop when total count reached to reduce the number of API calls
    #
    # Other entry types that are not listed here return 0
    # Related github issue: https://github.com/VocaDB/vocadb/issues/1766
    #
    # The API docs include three additional entryTypes: PV, DiscussionTopic, User
    # but these do not return anything

    entry_matrix = {
        entry_type: {edit_type: 0 for edit_type in get_args(Edit_type)}
        for entry_type in get_args(Entry_type)
    }
    # {'Song': {'Created': 0, 'Updated': 0, 'Deleted': 0}, ... 'ReleaseEventSeries': {'Created': 0, 'Updated': 0, 'Deleted': 0}}

    api_url = f"{WEBSITE}/api/activityEntries"
    params = {"maxResults": 1, "getTotalCount": True, "userId": user_id}

    if since:
        params["since"] = since

    if before:
        params["before"] = before

    total_count = fetch_json(api_url, params=params)["totalCount"]
    print(f"Total edits: {total_count}")

    combinations = [  # Sorted by how common they are
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
        count = fetch_json(api_url, params=params)["totalCount"]
        if count > 0:
            entry_matrix[entry_type][edit_type] = count
            print(
                f"{entry_type}, {edit_type}: Total count is now {total_count} - {count} = {total_count - count}"
            )
            total_count -= count
        print((edit_type, entry_type, count))

    print(entry_matrix)
    if total_count != 0:
        print(f"Count mismatch {total_count}, possible new activity after")
    return entry_matrix


@cache_with_expiration(days=1)
def get_user_profile(username: str) -> dict:
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


def get_monthly_count(year: int, month: int, count_func) -> int:
    logger.debug(f"Calculating monthly count for: {year}-{month}")

    a, b = get_month_strings(year, month)
    logger.debug(f"Corresponding date strings: {a} - {b}")

    month_is_over(year, month)
    return count_func(b) - count_func(a)


@cache_without_expiration()
def get_comment_count_before(before_date: str) -> int:
    api_url = f"{WEBSITE}/api/comments"
    params = {"before": before_date}
    return fetch_cached_totalcount(api_url, params=params)


def get_monthly_comment_count(year: int, month: int) -> int:
    return get_monthly_count(year, month, get_comment_count_before)

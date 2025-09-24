from datetime import datetime
from typing import get_args

from vdbpy.api.activity import parse_edits
from vdbpy.config import WEBSITE
from vdbpy.types import Edit_type, Entry_type, UserEdit, UserGroup
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.data import get_monthly_count
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_all_items_between_dates,
    fetch_json,
    fetch_json_items,
)

logger = get_logger()

USER_API_URL = f"{WEBSITE}/api/users"
ACTIVITY_API_URL = f"{WEBSITE}/api/activityEntries"

# TOOD: Type UserEntry


@cache_with_expiration(days=7)
def get_username_by_id(user_id: int, include_usergroup=False) -> str:
    user_api_url = f"{USER_API_URL}/{user_id}"
    data = fetch_json(user_api_url)
    if include_usergroup:
        return f"{data['name']} ({data['groupId']})"
    return data["name"]


@cache_with_expiration(days=1)
def get_user_profile_by_username(username: str) -> dict:
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


def get_user_profile_by_id(user_id: int) -> dict:
    username = get_username_by_id(user_id)
    return get_user_profile_by_username(username)


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

    print(f"User id not found with username '{username}' and mode '{mode}'")
    return ("", 0)


@cache_with_expiration(days=7)
def find_user_by_username(username: str) -> tuple[str, int]:
    # Available values : Auto, Partial, StartsWith, Exact, Words

    exact_match = find_user_by_username_and_mode(username, "Exact")
    if exact_match[1]:
        return exact_match

    return find_user_by_username_and_mode(username, "Partial")


# ------------------------------------------- #


@cache_with_expiration(days=7)
def get_rated_songs_by_user_id(user_id: int, extra_params=None):
    logger.info(f"Fetching rated songs for user id {user_id}")
    api_url = f"{USER_API_URL}/{user_id}/ratedSongs"
    rated_songs = fetch_json_items(api_url, extra_params)
    logger.info(f"Found total of {len(rated_songs)} rated songs.")
    return rated_songs


@cache_with_expiration(days=7)
def get_albums_by_user_id(user_id: int, extra_params=None):
    logger.info(f"Fetching albums for user id {user_id}")
    api_url = f"{USER_API_URL}/{user_id}/albums"
    albums = fetch_json_items(api_url, extra_params)
    logger.info(f"Found total of {len(albums)} albums.")
    return albums


@cache_with_expiration(days=7)
def get_followed_artists_by_user_id(user_id: int, extra_params=None):
    logger.info(f"Fetching followed artists for user id {user_id}")
    api_url = f"{USER_API_URL}/{user_id}/followedArtists"
    followed_artists = fetch_json_items(api_url, extra_params)
    if followed_artists:
        followed_artists = [ar["artist"] for ar in followed_artists]
    logger.info(f"Found total of {len(followed_artists)} followed artists")
    return followed_artists


def get_created_entries_by_username(username: str) -> list[UserEdit]:
    # Also includes deleted entries
    username, user_id = find_user_by_username(username)
    params = {
        "userId": user_id,
        "fields": "Entry,ArchivedVersion",
        "editEvent": "Created",
    }

    logger.debug(f"Fetching created entries by user '{username}' ({user_id})")
    return parse_edits(fetch_all_items_between_dates(ACTIVITY_API_URL, params=params, page_size=500))


def get_edits_by_username(username: str) -> list[UserEdit]:
    # Also includes deleted entries
    username, user_id = find_user_by_username(username)
    params = {
        "userId": user_id,
        "fields": "Entry,ArchivedVersion",
    }

    logger.debug(f"Fetching edits by user '{username}' ({user_id})")
    return parse_edits(fetch_all_items_between_dates(ACTIVITY_API_URL, params=params, page_size=500))

@cache_with_expiration(days=1)
def get_entry_matrix_by_user_id(user_id: int, since="", before=""):
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

    params = {"maxResults": 1, "getTotalCount": True, "userId": user_id}

    if since:
        params["since"] = since

    if before:
        params["before"] = before

    total_count = fetch_json(ACTIVITY_API_URL, params=params)["totalCount"]
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
        count = fetch_json(ACTIVITY_API_URL, params=params)["totalCount"]
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


def get_monthly_user_count(year: int, month: int) -> int:
    return get_monthly_count(year, month, USER_API_URL, param_name="joinDateBefore")


def get_user_account_age_by_user_id(user_id: int) -> int:
    """Get user account age in days."""
    username = get_username_by_id(user_id)
    creation_date = parse_date(get_user_profile_by_username(username)["createDate"])
    today = datetime.now()
    return (today - creation_date).days


def get_user_group_by_user_id(user_id: int) -> UserGroup:
    return fetch_json(f"{USER_API_URL}/{user_id}")["groupId"]


# -------------------------------------- #


def send_message(
    session, receiver_username: str, subject: str, message: str, sender_id: int, prompt=True
):
    url = f"{USER_API_URL}/{sender_id}/messages"

    data = {
        "body": message,
        "highPriority": False,
        "receiver": {"name": receiver_username},
        "sender": {"id": sender_id},
        "subject": subject,
    }

    if prompt:
        logger.info(f"{'---' * 10}\nTO='{receiver_username}' SUBJECT='{subject}'\n{message}\n{'---' * 10}")

        _ = input("Press enter to send...")
    message_request = session.post(url, json=data)
    message_request.raise_for_status()

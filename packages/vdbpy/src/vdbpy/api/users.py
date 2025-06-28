import requests

from vdbpy.config import WEBSITE
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.data import split_list
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json, fetch_json_items, fetch_totalcount

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

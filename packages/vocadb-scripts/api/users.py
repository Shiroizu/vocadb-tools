import requests

from utils.cache import cache_with_expiration
from utils.data import split_list
from utils.network import fetch_all_json_items, fetch_totalcount


@cache_with_expiration(days=7)
def get_rated_songs(user_id: int, extra_params=None):
    print(f"Fetching rated songs for user id {user_id}")
    api_url = f"https://vocadb.net/api/users/{user_id}/ratedSongs"
    rated_songs = fetch_all_json_items(api_url, extra_params)
    print(f"Found total of {len(rated_songs)} rated songs")
    return rated_songs


@cache_with_expiration(days=7)
def get_followed_artists(user_id: int, extra_params=None):
    print(f"Fetching followed artists for user id {user_id}")
    api_url = f"https://vocadb.net/api/users/{user_id}/followedArtists"
    followed_artists = fetch_all_json_items(api_url, extra_params)
    if followed_artists:
        followed_artists = [ar["artist"] for ar in followed_artists]
    print(f"Found total of {len(followed_artists)} followed artists")
    return followed_artists

@cache_with_expiration(days=1000)
def get_user_count(before_date: str):
    api_url = "https://vocadb.net/api/users"
    params = {"joinDateBefore": before_date}
    return fetch_totalcount(api_url, params=params)

def delete_notifications(session: requests.Session, user_id: int, notification_ids: list[str]):
    print(f"Got total of {len(notification_ids)} notifications to delete.")
    for sublist in split_list(notification_ids):
        # https://vocadb.net/api/users/329/messages?messageId=1947289&messageId=1946744&messageId=
        deletion_url = f"https://vocadb.net/api/users/{user_id}/messages?"
        query = [f"messageId={notif_id}" for notif_id in sublist]
        deletion_url += "&".join(query)
        _ = input(f"Press enter to delete {len(sublist)} notifications")
        deletion_request = session.delete(deletion_url)
        deletion_request.raise_for_status()

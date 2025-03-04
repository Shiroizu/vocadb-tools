from utils.network import fetch_all_json_items


def get_rated_songs(user_id: int, extra_params=None):
    print(f"Fetching rated songs for user id {user_id}")
    api_url = f"https://vocadb.net/api/users/{user_id}/ratedSongs"
    rated_songs = fetch_all_json_items(api_url, extra_params)
    print(f"Found total of {len(rated_songs)} rated songs")
    return rated_songs


def get_followed_artists(user_id: int, extra_params=None):
    print(f"Fetching followed artists for user id {user_id}")
    api_url = f"https://vocadb.net/api/users/{user_id}/followedArtists"
    followed_artists = fetch_all_json_items(api_url, extra_params)
    print(f"Found total of {len(followed_artists)} followed artists")
    return followed_artists

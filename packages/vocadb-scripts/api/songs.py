from utils.network import fetch_all_json_items


def get_songs_by_artist(artist_id: int, params: dict):
    url = "https://vocadb.net/api/songs"
    params["artistId[]"] = artist_id
    return fetch_all_json_items(url, params)

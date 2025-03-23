from utils.network import fetch_all_json_items

SONG_API_URL = "https://vocadb.net/api/songs"

def get_songs_by_artist(artist_id: int, params: dict):
    params["artistId[]"] = artist_id
    return fetch_all_json_items(SONG_API_URL, params)

def get_songs_by_tag(tag_id: int, params: dict):
    params["tagId[]"] = tag_id
    return fetch_all_json_items(SONG_API_URL, params)

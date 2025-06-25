from vdbpy.config import WEBSITE
from vdbpy.utils.network import fetch_json_items

SONG_API_URL = f"{WEBSITE}/api/songs"


def get_songs_by_artist(artist_id: int, params: dict):
    params["artistId[]"] = artist_id
    return fetch_json_items(SONG_API_URL, params)


def get_songs_by_tag(tag_id: int, params: dict):
    params["tagId[]"] = tag_id
    return fetch_json_items(SONG_API_URL, params)

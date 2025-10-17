from vdbpy.config import WEBSITE
from vdbpy.utils.network import fetch_json, fetch_json_items

ALBUM_API_URL = f"{WEBSITE}/api/albums"
SONG_API_URL = f"{WEBSITE}/api/songs"

# TODO: Type AlbumEntry


def get_albums(params):
    return fetch_json_items(ALBUM_API_URL, params=params)


def get_album(params):
    result = fetch_json(ALBUM_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_album_by_id(album_id, fields=""):
    params = {"fields": fields} if fields else {}
    url = f"{ALBUM_API_URL}/{album_id}"
    return fetch_json(url, params=params)


def get_albums_by_tag_id(tag_id: int):
    params = {"tagId[]": tag_id}
    return get_albums(params=params)

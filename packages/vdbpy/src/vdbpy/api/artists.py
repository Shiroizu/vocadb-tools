from vdbpy.config import WEBSITE
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.network import fetch_json, fetch_json_items, fetch_totalcount

ARTIST_API_URL = f"{WEBSITE}/api/artists"
SONG_API_URL = f"{WEBSITE}/api/songs"


def get_artists(params):
    return fetch_json_items(ARTIST_API_URL, params=params)


@cache_with_expiration(days=1)
def get_artist_by_id(artist_id, fields=""):
    params = {"fields": fields} if fields else {}
    url = f"{ARTIST_API_URL}/{artist_id}"
    return fetch_json(url, params=params)


def get_artists_by_tag_id(tag_id: int):
    params = {"tagId[]": tag_id}
    return get_artists(params=params)


@cache_with_expiration(days=7)
def get_song_count_by_artist_id(artist_id: int, only_main_songs=False, extra_params=None):
    params = extra_params if extra_params else {}
    params["artistId[]"] = artist_id
    if only_main_songs:
        params["artistParticipationStatus"] = "OnlyMainAlbums"  # type: ignore
    return fetch_totalcount(SONG_API_URL, params)


@cache_with_expiration(days=1000)
def get_base_voicebank_by_artist_id(artist_id: int, recursive=True) -> int:
    """Get base voicebank id if it exists. Return current id otherwise."""
    params = {"fields": "baseVoiceBank"}
    next_base_vb_id = artist_id
    while True:
        url = f"{ARTIST_API_URL}/{next_base_vb_id}"
        next_base_vb = fetch_json(url, params=params)
        if "baseVoicebank" in next_base_vb and recursive:
            next_base_vb_id = next_base_vb["baseVoicebank"]["id"]
            continue
        return next_base_vb

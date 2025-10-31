from vdbpy.config import ARTIST_API_URL, SONG_API_URL, USER_API_URL
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
    fetch_totalcount,
)

type Artist = dict  # TODO


def get_artists(params) -> list[Artist]:
    return fetch_json_items(ARTIST_API_URL, params=params)


def get_artist(params) -> Artist:
    result = fetch_json(ARTIST_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_artists_with_total_count(params, max_results=10**9) -> tuple[list[Artist], int]:
    return fetch_json_items_with_total_count(
        ARTIST_API_URL, params=params, max_results=max_results
    )


def get_artist_by_id(artist_id, fields="") -> Artist:
    params = {"fields": fields} if fields else {}
    url = f"{ARTIST_API_URL}/{artist_id}"
    return fetch_json(url, params=params)


def get_artists_by_tag_id(tag_id: int) -> list[Artist]:
    params = {"tagId[]": tag_id}
    return get_artists(params=params)


@cache_with_expiration(days=1)
def get_song_count_by_artist_id_1d(
    artist_id: int, only_main_songs=False, extra_params=None
) -> int:
    params = extra_params if extra_params else {}
    params["artistId[]"] = artist_id
    if only_main_songs:
        params["artistParticipationStatus"] = "OnlyMainAlbums"  # type: ignore
    return fetch_totalcount(SONG_API_URL, params)


def get_base_voicebank_by_artist_id(artist_id: int, recursive=True) -> Artist:
    """Get base voicebank id if it exists. Return current id otherwise."""
    params = {"fields": "baseVoiceBank"}
    next_base_vb_id = artist_id
    while True:
        url = f"{ARTIST_API_URL}/{next_base_vb_id}"
        next_base_vb = fetch_json(url, params=params)  # FIX
        if "baseVoicebank" in next_base_vb and recursive:
            next_base_vb_id = next_base_vb["baseVoicebank"]["id"]
            continue
        return next_base_vb


@cache_without_expiration()
def get_cached_base_voicebank_by_artist_id(artist_id: int, recursive=True) -> Artist:
    return get_base_voicebank_by_artist_id(artist_id, recursive)


@cache_with_expiration(days=7)
def get_followed_artists_by_user_id_7d(user_id: int, extra_params=None) -> list[Artist]:
    api_url = f"{USER_API_URL}/{user_id}/followedArtists"
    followed_artists = fetch_json_items(api_url, extra_params)
    if followed_artists:
        followed_artists = [ar["artist"] for ar in followed_artists]
    return followed_artists

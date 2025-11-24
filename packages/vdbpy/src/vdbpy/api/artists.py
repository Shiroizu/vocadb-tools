from typing import Any

from vdbpy.config import ARTIST_API_URL, SONG_API_URL, USER_API_URL
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
    fetch_total_count,
)

logger = get_logger()


def get_artists(params: dict[Any, Any] | None) -> list[dict[Any, Any]]:
    return fetch_json_items(ARTIST_API_URL, params=params)


def get_artist_by_id(artist_id: int, fields: list[str] | None = None) -> dict[Any, Any]:
    params = {"fields": ",".join(fields)} if fields else None
    return fetch_json(f"{ARTIST_API_URL}/{artist_id}", params=params)


def get_json_artists_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[dict[Any, Any]], int]:
    return fetch_json_items_with_total_count(
        ARTIST_API_URL, params=params, max_results=max_results
    )


def get_artists_by_tag_id(tag_id: int) -> list[dict[Any, Any]]:
    params = {"tagId[]": tag_id}
    return get_artists(params=params)


@cache_with_expiration(days=1)
def get_song_count_by_artist_id_1d(
    artist_id: int,
    only_main_songs: bool = False,
    extra_params: dict[Any, Any] | None = None,
) -> int:
    params = extra_params if extra_params else {}
    params["artistId[]"] = artist_id
    if only_main_songs:
        params["artistParticipationStatus"] = "OnlyMainAlbums"
    return fetch_total_count(SONG_API_URL, params)


# def get_base_voicebank_id_by_artist_id(artist_id: int, recursive: bool = True) ->
# Artist:
#     """Get base voicebank id if it exists. Return current id otherwise."""
#     params = {"fields": "baseVoiceBank"}
#     next_base_vb_id = artist_id
#     while True:
#         url = f"{ARTIST_API_URL}/{next_base_vb_id}"
#         next_base_vb = fetch_json(url, params=params)  # TODO FIX
#         if "baseVoicebank" in next_base_vb and recursive:
#             next_base_vb_id = next_base_vb["baseVoicebank"]["id"]
#             continue
#         return next_base_vb


# @cache_without_expiration()
# def get_cached_base_voicebank_by_artist_id(
#     artist_id: int, recursive: bool = True
# ) -> Artist:
#     return get_base_voicebank_id_by_artist_id(artist_id, recursive)


@cache_with_expiration(days=7)
def get_followed_artists_by_user_id_7d(
    user_id: int, extra_params: dict[Any, Any] | None = None
) -> list[dict[Any, Any]]:
    api_url = f"{USER_API_URL}/{user_id}/followedArtists"
    followed_artists = fetch_json_items(api_url, extra_params)
    if followed_artists:
        followed_artists = [ar["artist"] for ar in followed_artists]
    return followed_artists

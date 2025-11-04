from typing import Any

from vdbpy.config import ALBUM_API_URL, USER_API_URL
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)

logger = get_logger()

type Album = dict[Any, Any]  # TODO implement


def get_albums(params: dict[Any, Any] | None) -> list[Album]:
    return fetch_json_items(ALBUM_API_URL, params=params)


def get_albums_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[Album], int]:
    return fetch_json_items_with_total_count(
        ALBUM_API_URL, params=params, max_results=max_results
    )


def get_album(params: dict[Any, Any] | None) -> Album:
    result = fetch_json(ALBUM_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_album_by_id(album_id: int, fields: str = "") -> Album:
    params = {"fields": fields} if fields else {}
    url = f"{ALBUM_API_URL}/{album_id}"
    return fetch_json(url, params=params)


def get_albums_by_tag_id(tag_id: int) -> list[Album]:
    params = {"tagId[]": tag_id}
    return get_albums(params=params)


@cache_with_expiration(days=7)
def get_albums_by_user_id_7d(
    user_id: int, extra_params: dict[Any, Any] | None = None
) -> list[Album]:
    logger.info(f"Fetching albums for user id {user_id}")
    api_url = f"{USER_API_URL}/{user_id}/albums"
    albums = fetch_json_items(api_url, extra_params)
    logger.info(f"Found total of {len(albums)} albums.")
    return albums

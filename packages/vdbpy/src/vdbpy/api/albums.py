from typing import Any

import requests

from vdbpy.config import ALBUM_API_URL, USER_API_URL
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_json_items,
    fetch_json_items_with_total_count,
)

logger = get_logger()


def get_albums(params: dict[Any, Any] | None) -> list[dict[Any, Any]]:
    return fetch_json_items(ALBUM_API_URL, params=params)


def get_json_albums_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[dict[Any, Any]], int]:
    return fetch_json_items_with_total_count(
        ALBUM_API_URL, params=params, max_results=max_results
    )


def get_albums_by_tag_id(tag_id: int) -> list[dict[Any, Any]]:
    params = {"tagId[]": tag_id}
    return get_albums(params=params)


def get_albums_by_user_id(
    user_id: int,
    extra_params: dict[Any, Any] | None = None,
    session: requests.Session | None = None,
) -> list[dict[Any, Any]]:
    """Fetch albums in the user's collection."""
    from vdbpy.api.users import has_public_album_collection  # noqa: PLC0415

    if has_public_album_collection(user_id) is False:
        return []
    logger.info(f"Fetching albums for user id {user_id}")
    api_url = f"{USER_API_URL}/{user_id}/albums"
    params = {**(extra_params or {})}
    albums = fetch_json_items(api_url, params=params, session=session)
    logger.info(f"Found total of {len(albums)} albums.")
    return albums


def get_cached_albums_by_user_id(
    user_id: int, session: requests.Session | None = None
) -> list[dict[Any, Any]]:
    """Return albums from the user library cache (always fetched with Artists field)."""
    from vdbpy.api.user_library import get_user_library  # noqa: PLC0415

    return get_user_library(
        user_id, collections=frozenset({"albums"}), session=session
    ).albums

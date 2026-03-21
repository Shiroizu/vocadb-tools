from typing import Any

from vdbpy.config import TAG_API_URL
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)


def get_tag_by_id(tag_id: int, fields: list[str] | None = None) -> dict[Any, Any]:
    params = {"fields": ",".join(fields)} if fields else None
    return fetch_json(f"{TAG_API_URL}/{tag_id}", params=params)


@cache_with_expiration(days=7)
def get_tag_by_id_7d(tag_id: int, fields: list[str] | None = None) -> dict[Any, Any]:
    return get_tag_by_id(tag_id, fields=fields)


def get_tag_details_by_id(tag_id: int) -> dict[Any, Any]:
    return fetch_json(f"{TAG_API_URL}/{tag_id}/details")


@cache_with_expiration(days=7)
def get_tag_details_by_id_7d(tag_id: int) -> dict[Any, Any]:
    return get_tag_details_by_id(tag_id)


def get_tags(params: dict[Any, Any] | None) -> list[dict[Any, Any]]:
    return fetch_json_items(TAG_API_URL, params=params)


def get_json_tags_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[dict[Any, Any]], int]:
    return fetch_json_items_with_total_count(
        TAG_API_URL, params=params, max_results=max_results
    )

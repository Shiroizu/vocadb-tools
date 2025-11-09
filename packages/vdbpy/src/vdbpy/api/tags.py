from typing import Any

from vdbpy.config import TAG_API_URL
from vdbpy.types.tags import Tag
from vdbpy.utils.network import (
    fetch_json_items,
    fetch_json_items_with_total_count,
)


def get_tags(params: dict[Any, Any] | None) -> list[Tag]:
    return fetch_json_items(TAG_API_URL, params=params)


def get_tags_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[Tag], int]:
    return fetch_json_items_with_total_count(
        TAG_API_URL, params=params, max_results=max_results
    )

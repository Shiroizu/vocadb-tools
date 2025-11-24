from typing import Any

from vdbpy.config import TAG_API_URL
from vdbpy.utils.network import (
    fetch_json_items,
    fetch_json_items_with_total_count,
)


def get_tags(params: dict[Any, Any] | None) -> list[dict[Any, Any]]:
    return fetch_json_items(TAG_API_URL, params=params)


def get_json_tags_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[dict[Any, Any]], int]:
    return fetch_json_items_with_total_count(
        TAG_API_URL, params=params, max_results=max_results
    )

from typing import Any

from vdbpy.config import SERIES_API_URL
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)


def get_many_series(params: dict[Any, Any] | None) -> list[dict[Any, Any]]:
    return fetch_json_items(SERIES_API_URL, params=params)


def get_json_many_series_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[dict[Any, Any]], int]:
    return fetch_json_items_with_total_count(
        SERIES_API_URL, params=params, max_results=max_results
    )


def get_one_series(params: dict[Any, Any] | None) -> dict[Any, Any]:
    result = fetch_json(SERIES_API_URL, params=params)
    return result["items"][0] if result["items"] else {}

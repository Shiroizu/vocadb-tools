from typing import Any

from vdbpy.config import VENUE_API_URL
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)


def get_venues(params: dict[Any, Any] | None) -> list[dict[Any, Any]]:
    return fetch_json_items(VENUE_API_URL, params=params)


def get_json_venues_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[dict[Any, Any]], int]:
    return fetch_json_items_with_total_count(
        VENUE_API_URL, params=params, max_results=max_results
    )


def get_venue(params: dict[Any, Any] | None) -> dict[Any, Any]:
    result = fetch_json(VENUE_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_venue_by_id(venue_id: int, fields: str = "") -> dict[Any, Any]:
    params = {"fields": fields} if fields else {}
    url = f"{VENUE_API_URL}/{venue_id}"
    return fetch_json(url, params=params)

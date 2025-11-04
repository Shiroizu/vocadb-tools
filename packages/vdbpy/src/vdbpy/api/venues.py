from typing import Any

from vdbpy.config import VENUE_API_URL
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)

type Venue = dict[Any, Any]  # TODO implement


def get_venues(params: dict[Any, Any] | None) -> list[Venue]:
    return fetch_json_items(VENUE_API_URL, params=params)


def get_venues_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[Venue], int]:
    return fetch_json_items_with_total_count(
        VENUE_API_URL, params=params, max_results=max_results
    )


def get_venue(params: dict[Any, Any] | None) -> Venue:
    result = fetch_json(VENUE_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_venue_by_id(venue_id: int, fields: str = "") -> Venue:
    params = {"fields": fields} if fields else {}
    url = f"{VENUE_API_URL}/{venue_id}"
    return fetch_json(url, params=params)

from typing import Any

from vdbpy.config import EVENT_API_URL
from vdbpy.types.events import ReleaseEvent, ReleaseEventDetails
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)


def get_events(params: dict[Any, Any] | None) -> list[ReleaseEvent]:
    return fetch_json_items(EVENT_API_URL, params=params)


def get_events_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[ReleaseEvent], int]:
    return fetch_json_items_with_total_count(
        EVENT_API_URL, params=params, max_results=max_results
    )


def get_event_details_by_event_id(
    event_id: int, params: dict[Any, Any] | None = None
) -> ReleaseEventDetails:
    params = {} if params is None else params
    api_url = f"{EVENT_API_URL}/{event_id}"
    return fetch_json(api_url, params=params)

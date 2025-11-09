from typing import Any

from vdbpy.config import SERIES_API_URL
from vdbpy.types.series import ReleaseEventSeriesEntry
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)


def get_many_series(params: dict[Any, Any] | None) -> list[ReleaseEventSeriesEntry]:
    return fetch_json_items(SERIES_API_URL, params=params)


def get_many_series_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[ReleaseEventSeriesEntry], int]:
    return fetch_json_items_with_total_count(
        SERIES_API_URL, params=params, max_results=max_results
    )


def get_one_series(params: dict[Any, Any] | None) -> ReleaseEventSeriesEntry:
    result = fetch_json(SERIES_API_URL, params=params)
    return result["items"][0] if result["items"] else {}

from vdbpy.config import WEBSITE
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)

SERIES_API_URL = f"{WEBSITE}/api/releaseEventSeries"
# TODO: Type SeriesEntry


def get_many_series(params) -> list:
    return fetch_json_items(SERIES_API_URL, params=params)


def get_many_series_with_total_count(params, max_results=10**9) -> tuple[list, int]:
    return fetch_json_items_with_total_count(
        SERIES_API_URL, params=params, max_results=max_results
    )


def get_one_series(params):
    result = fetch_json(SERIES_API_URL, params=params)
    return result["items"][0] if result["items"] else {}

from vdbpy.config import WEBSITE
from vdbpy.utils.network import fetch_json, fetch_json_items

SERIES_API_URL = f"{WEBSITE}/api/releaseEventSeries"
# TODO: Type SeriesEntry


def get_many_series(params):
    return fetch_json_items(SERIES_API_URL, params=params)


def get_one_series(params):
    result = fetch_json(SERIES_API_URL, params=params)
    return result["items"][0] if result["items"] else {}

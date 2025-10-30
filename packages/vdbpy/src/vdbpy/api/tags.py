from vdbpy.config import TAG_API_URL
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
)

type Tag = dict  # TODO


def get_tags(params) -> list[Tag]:
    return fetch_json_items(TAG_API_URL, params=params)


def get_tags_with_total_count(params, max_results=10**9) -> tuple[list[Tag], int]:
    return fetch_json_items_with_total_count(
        TAG_API_URL, params=params, max_results=max_results
    )


def get_tag(params) -> Tag:
    result = fetch_json(TAG_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_tag_by_id(tag_id, fields="") -> Tag:
    params = {"fields": fields} if fields else {}
    url = f"{TAG_API_URL}/{tag_id}"
    return fetch_json(url, params=params)

import time
from datetime import UTC, datetime
from typing import Any

import requests

from vdbpy.config import ACTIVITY_API_URL
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger

logger = get_logger()
BASE_DELAY = 0.5
BASE_TIMEOUT = 20
PAGE_SIZE = 50
TOTAL_COUNT_WARNING = 5000

# TODO user agent


def fetch_text(
    url: str,
    session: requests.Session | None = None,
    params: dict[Any, Any] | None = None,
) -> str:
    logger.debug(f"Fetching text from url '{url}' with params {params}")
    r = (
        session.get(url, params=params)
        if session
        else requests.get(url, params=params, timeout=BASE_TIMEOUT)
    )
    if params:
        logger.debug(f"Parsed URL: {r.url}")
    r.raise_for_status()
    time.sleep(BASE_DELAY)
    if r.encoding == "ISO-8859-1":
        logger.debug("Converting from ISO-8859-1 to UTF-8")
        return r.text.encode("ISO-8859-1").decode("utf-8")
    return r.text


def fetch_json(
    url: str,
    session: requests.Session | None = None,
    params: dict[Any, Any] | tuple[Any, Any] | None = None,
) -> dict[Any, Any]:
    logger.debug(f"Fetching JSON from url {url} with params {params}")

    r = (
        session.get(url, params=params)
        if session
        else requests.get(url, params=params, timeout=BASE_TIMEOUT)
    )

    if params:
        logger.debug(f"Parsed URL: {r.url}")
    r.raise_for_status()
    time.sleep(BASE_DELAY)
    return r.json()


@cache_without_expiration()
def fetch_cached_json(
    url: str,
    session: requests.Session | None = None,
    params: dict[Any, Any] | None = None,
) -> dict[Any, Any]:
    return fetch_json(url, session=session, params=params)


def fetch_json_items_with_total_count(
    url: str,
    params: dict[Any, Any] | None = None,  # TODO BaseSearchParams type
    session: requests.Session | None = None,
    max_results: int = 10**9,
) -> tuple[list[Any], int]:
    page_size: int = 50
    params = params.copy() if params is not None else {}
    logger.info(f"Fetching all items based on '{url}' with params {params}")
    if "maxResults" in params:
        if max_results != 10**9:
            logger.warning("Duplicate max result argument provided!")
            logger.warning(f"({params['maxResults'] and max_results})")
        max_results = params["maxResults"]
        logger.info(f"  Stopping after {max_results} results")
    if url == ACTIVITY_API_URL:
        logger.warning(f"Start param not supported for '{ACTIVITY_API_URL}'!")
        logger.warning("Use fetch_all_items_between_dates instead.")
        raise NotImplementedError
    all_items: list[Any] = []
    page = 1
    params["maxResults"] = min(page_size, max_results)
    params["getTotalCount"] = True
    warned = False
    while True:
        params["start"] = str(page_size * (page - 1))
        json = fetch_json(url, session=session, params=params)
        items = json["items"]
        total_count = json["totalCount"]

        if min(total_count, max_results) > TOTAL_COUNT_WARNING and not warned:
            logger.warning(
                f"Total count {total_count} is higher than {TOTAL_COUNT_WARNING}!"
            )
            _ = input("Press enter to continue...")
            warned = True

        all_items.extend(items)
        logger.info(f"  Page {page}/{1 + (total_count // page_size)}")
        if len(all_items) >= max_results:
            break
        if len(items) < page_size:
            break
        page += 1
    return all_items[:max_results], total_count


def fetch_json_items(
    url: str,
    params: dict[Any, Any] | None = None,
    session: requests.Session | None = None,
    max_results: int = 10**9,
) -> list[Any]:
    return fetch_json_items_with_total_count(url, params, session, max_results)[0]


def fetch_total_count(api_url: str, params: dict[Any, Any] | None = None) -> int:
    logger.debug(f"Fetching total count for '{api_url} with params {params}'")
    params = params.copy() if params is not None else {}
    params["maxResults"] = 1
    params["getTotalCount"] = True
    total_count = fetch_json(api_url, params=params)["totalCount"]
    if not total_count:
        return 0
    return int(total_count)


@cache_with_expiration(days=30)
def fetch_total_count_30d(api_url: str, params: dict[Any, Any] | None = None) -> int:
    return fetch_total_count(api_url, params=params)


def fetch_cached_total_count(api_url: str, params: dict[Any, Any] | None = None) -> int:
    params = params.copy() if params is not None else {}
    params["maxResults"] = 1
    params["getTotalCount"] = True
    total_count = fetch_cached_json(api_url, params=params)["totalCount"]
    return int(total_count)


def fetch_all_items_between_dates(
    api_url: str,
    since: str = "2000-01-01T00:00:00Z",
    before: str = "2100-01-01T00:00:00Z",
    date_indicator: str = "createDate",
    params: dict[Any, Any] | None = None,
    page_size: int = 50,
) -> list[Any]:
    """Get all items by decreasing 'before' parameter incrementally."""
    params = params.copy() if params is not None else {}
    params["maxResults"] = page_size
    params["before"] = before
    params["since"] = since

    all_items: list[Any] = []

    logger.debug(f"Fetching all '{api_url}' items from '{since}' to '{before}'...")
    now = datetime.now(tz=UTC)

    while True:
        if parse_date(params["before"]) < now:
            logger.debug("Fetching cached json since beforedate is in the past...")
            items = fetch_cached_json(api_url, params=params)["items"]
        else:
            logger.debug("Skipping cache, date is still ongoing or in the future...")
            items = fetch_json(api_url, params=params)["items"]
        logger.debug(
            f"Fetching items from '{params['since']}' to '{params['before']}'..."
        )

        if not items:
            logger.info("No items found, stopping.")
            break

        all_items.extend(items)
        logger.debug(f"Found {len(items)} items.")

        if len(items) < page_size:
            logger.debug(f"Less than {page_size} items, stopping.")
            break

        params["before"] = items[-1][date_indicator]

    return all_items

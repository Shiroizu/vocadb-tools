import time
from collections.abc import Callable
from typing import Any

import requests
from requests import Response

from vdbpy.config import ACTIVITY_API_URL
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.logger import get_logger

logger = get_logger()
BASE_DELAY = 1
BASE_TIMEOUT = 20
PAGE_SIZE = 50
TOTAL_COUNT_WARNING = 5000
RETRY_COUNT = 5
RETRY_TIMER = 10

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
    if "localhost" not in url:
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

    retry_count = 1
    while retry_count <= RETRY_COUNT:
        r: Response | None = None
        try:
            r = (
                session.get(url, params=params)
                if session
                else requests.get(url, params=params, timeout=BASE_TIMEOUT)
            )
            if params:
                logger.debug(f"Parsed URL: {r.url}")
            r.raise_for_status()
            if "localhost" not in url:
                time.sleep(BASE_DELAY)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.HTTPError,
        ):
            if not r or r.status_code == 404:  # noqa: PLR2004
                logger.warning(f"Not found: {url}")
                return {}
            logger.warning(f"Connection issues with '{r.url}'")
            retry_count += 1
            logger.warning(f"Retry attempt #{retry_count}")
            logger.warning(f"Trying again in {RETRY_TIMER} seconds...")
            time.sleep(RETRY_TIMER)
            continue
        return r.json()

    msg = f"Failed to fetch JSON from {url} after {RETRY_COUNT} retries"
    raise Exception(msg)  # noqa: TRY002


@cache_without_expiration()
def fetch_cached_json(
    url: str,
    session: requests.Session | None = None,
    params: dict[Any, Any] | None = None,
) -> dict[Any, Any]:
    return fetch_json(url, session=session, params=params)


def fetch_json_items_with_total_count(  # noqa: PLR0915
    url: str,
    params: dict[Any, Any] | None = None,  # TODO BaseSearchParams type
    session: requests.Session | None = None,
    max_results: int = 10**9,
    limit: int | Callable[..., bool] | None = None,
) -> tuple[list[Any], int]:
    if limit == 0:
        return [], True
    page_size: int = 50
    params = params.copy() if params is not None else {}
    logger.debug(f"Fetching all items based on '{url}' with params {params}")
    logger.debug(f"Using limit: {limit}")
    if "maxResults" in params:
        if max_results != 10**9:
            logger.warning("Duplicate max result argument provided!")
            logger.warning(f"({params['maxResults'] and max_results})")
        max_results = params["maxResults"]
        logger.debug(f"  Stopping after {max_results} results")
    if url == ACTIVITY_API_URL:
        logger.warning(f"Start param not supported for '{ACTIVITY_API_URL}'!")
        logger.warning("Use fetch_all_items_between_dates instead.")
        raise NotImplementedError
    all_items: list[Any] = []
    total_count = 0
    params["maxResults"] = min(page_size, max_results)
    params["getTotalCount"] = True
    warned = False
    page = 1
    while True:
        params["start"] = str(page_size * (page - 1))
        json = fetch_json(url, session=session, params=params)
        if "items" not in json:
            logger.warning(f"Items not found in json: {json}")
            break
        items = json["items"]
        total_count = json["totalCount"]

        if min(total_count, max_results) > TOTAL_COUNT_WARNING and not warned:
            logger.warning(
                f"Total count {total_count} is higher than {TOTAL_COUNT_WARNING}!"
            )
            _ = input("Press enter to continue...")
            warned = True

        limit_reached = False
        if not items:
            logger.debug("No items found!")
            break
        logger.debug(
            f"Got {len(items)} items from {items[0]['id']} to {items[-1]['id']}"
        )
        for item in items:
            if isinstance(limit, int) and len(all_items) >= limit:
                logger.debug(f"Limit {limit} reached, stopping.")
                limit_reached = True
                break
            if callable(limit) and limit(item):
                logger.debug("Limit condition met, stopping.")
                limit_reached = True
                break
            all_items.append(item)
        if limit_reached:
            break

        if len(all_items) >= max_results:
            break
        if len(items) < page_size:
            break
        logger.info(f"  Page {page}/{1 + (total_count // page_size)}")
        page += 1
    return all_items[:max_results], total_count


def fetch_json_items(
    url: str,
    params: dict[Any, Any] | None = None,
    session: requests.Session | None = None,
    max_results: int = 10**9,
    limit: int | Callable[..., bool] | None = None,
) -> list[Any]:
    return fetch_json_items_with_total_count(url, params, session, max_results, limit)[
        0
    ]


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
    page_size: int = PAGE_SIZE,
    limit: int | Callable[..., bool] | None = None,
) -> tuple[list[Any], bool]:
    """Get all items by decreasing 'before' parameter incrementally.

    Duplicates are possible!
    """
    if limit == 0:
        return [], True
    params = params.copy() if params is not None else {}
    params["maxResults"] = page_size
    params["before"] = before
    params["since"] = since

    all_items: list[Any] = []

    logger.debug(f"Fetching all '{api_url}' items from '{since}' to '{before}'...")
    logger.debug(f"Using limit: {limit}")

    limit_reached = False
    while True:
        logger.debug(
            f"Fetching items from '{params['since']}' to '{params['before']}'..."
        )
        json = fetch_json(api_url, params=params)
        if "items" not in json:
            logger.warning(f"Items not found in json: {json}")
            break
        items = json["items"]
        if not items:
            logger.info("No items found, stopping.")
            break

        for item in items:
            if isinstance(limit, int) and len(all_items) >= limit:
                logger.info(f"Limit {limit} reached, stopping.")
                limit_reached = True
                break
            if callable(limit) and limit(item):
                logger.info("Limit condition met, stopping.")
                limit_reached = True
                break
            all_items.append(item)

        if limit_reached:
            break

        if len(items) < PAGE_SIZE:
            logger.debug(f"Less than {PAGE_SIZE} items, stopping.")
            break

        logger.debug(f"Found {len(items)} items.")
        params["before"] = items[-1][date_indicator]

    return all_items, limit_reached

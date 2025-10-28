import time
from datetime import UTC, datetime

import requests

from vdbpy.config import WEBSITE
from vdbpy.utils.cache import cache_without_expiration
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger

logger = get_logger()
BASE_DELAY = 0.5

ACTIVITY_API_URL = f"{WEBSITE}/api/activityEntries"


def fetch_text(url: str, session=requests, params=None):
    logger.debug(f"Fetching text from url '{url}' with params {params}")
    r = session.get(url, params=params)
    if params:
        logger.debug(f"Parsed URL: '{r.url}'")
    r.raise_for_status()
    time.sleep(BASE_DELAY)
    if r.encoding == "ISO-8859-1":
        logger.info("Converting from ISO-8859-1 to UTF-8")
        return r.text.encode("ISO-8859-1").decode("utf-8")
    return r.text


def fetch_json(url: str, session=requests, params=None):
    logger.debug(f"Fetching JSON from url '{url}' with params {params}")
    r = session.get(url, params=params)
    if params:
        logger.debug(f"Parsed URL: '{r.url}'")
    r.raise_for_status()
    time.sleep(BASE_DELAY)
    return r.json()


@cache_without_expiration()
def fetch_cached_json(url: str, session=requests, params=None):
    """Helper URL fetch function."""
    return fetch_json(url, session=session, params=params)


def fetch_json_items(
    url, params: dict | None = None, session=requests, max_results=10**9, page_size=50
) -> list:
    params = params if params is not None else {}
    logger.debug(f"Fetching all JSON items for url '{url}'")
    logger.debug(f"Params: {params}")
    if url == ACTIVITY_API_URL:
        logger.warning(f"Start param not supported for '{ACTIVITY_API_URL}'!")
        logger.warning("Use fetch_all_items_between_dates instead.")
    all_items = []
    page = 1
    if "maxResults" in params and max_results == 10**9:
        max_results = params["maxResults"]

    params = params if params is not None else {}
    params["maxResults"] = page_size
    params["getTotalCount"] = True
    while True:
        params["start"] = str(page_size * (page - 1))
        json = fetch_json(url, session=session, params=params)
        items = json["items"]
        totalcount = json["totalCount"]
        if not items:
            return all_items
        logger.debug(f"Page {page}/{1+(totalcount//page_size)}")
        all_items.extend(items)
        if len(all_items) >= max_results:
            return all_items[:max_results]
        page += 1


def fetch_json_items_with_total_count(
    url, params: dict | None = None, session=requests, max_results=10**9, page_size=50
) -> tuple[list, int]:
    params = params if params is not None else {}
    logger.debug(f"Fetching all JSON items with total count for url '{url}'")
    logger.debug(f"Params: {params}")
    if url == ACTIVITY_API_URL:
        logger.warning(f"Start param not supported for '{ACTIVITY_API_URL}'!")
        logger.warning("Use fetch_all_items_between_dates instead.")
    all_items = []
    page = 1
    params = params if params is not None else {}
    params["maxResults"] = page_size
    params["getTotalCount"] = True
    while True:
        params["start"] = str(page_size * (page - 1))
        json = fetch_json(url, session=session, params=params)
        items = json["items"]
        totalcount = json["totalCount"]

        if not items:
            return all_items, totalcount
        logger.info(f"Page {page}/{1+(totalcount//page_size)}")
        all_items.extend(items)

        if len(all_items) >= max_results:
            return all_items[:max_results], totalcount
        page += 1


def fetch_totalcount(api_url, params: dict | None = None) -> int:
    params = params if params is not None else {}
    params["maxResults"] = 1
    params["getTotalCount"] = True
    totalcount = fetch_json(api_url, params=params)["totalCount"]
    if not totalcount:
        return 0
    return int(totalcount)


def fetch_cached_totalcount(api_url, params: dict | None = None) -> int:
    params = params if params is not None else {}
    params["maxResults"] = 1
    params["getTotalCount"] = True
    totalcount = fetch_cached_json(api_url, params=params)["totalCount"]
    return int(totalcount)


def fetch_all_items_between_dates(
    api_url,
    since: str = "2000-01-01T00:00:00Z",
    before: str = "2100-01-01T00:00:00Z",
    date_indicator="createDate",
    params: dict | None = None,
    page_size=50,
) -> list:
    """Get all items between date strings by decreasing before parameter incrementally."""
    params = params if params is not None else {}
    params["maxResults"] = page_size
    params["before"] = before
    params["since"] = since

    all_items = []

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

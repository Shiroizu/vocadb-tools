import time

import requests

from vdbpy.utils.logger import get_logger

logger = get_logger()


def fetch_json(url: str, session=requests, params=None):
    logger.debug(f"Fetching JSON from url '{url}'")
    logger.debug(f"Params: {params}")
    r = session.get(url, params=params)
    logger.debug(f"Parsed URL: '{r.url}'")
    r.raise_for_status()
    time.sleep(0.5)
    return r.json()


def fetch_json_items(
    url, params: dict | None = None, session=requests, max_results=10**9
):
    logger.debug(f"Fetching all JSON items for url '{url}'")
    logger.debug(f"Params: {params}")
    all_items = []
    page = 1
    page_size = 50
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
        logger.info(f"Page {page}/{1+(totalcount//page_size)}")
        all_items.extend(items)
        if len(all_items) >= max_results:
            return all_items[:max_results]
        page += 1


def fetch_totalcount(api_url, params: dict | None = None) -> int:
    params = params if params is not None else {}
    params["maxResults"] = 1
    params["getTotalCount"] = True
    totalcount = fetch_json(api_url, params=params)["totalCount"]
    return int(totalcount)

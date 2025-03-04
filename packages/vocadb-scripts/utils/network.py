import time

import requests


def fetch_json(url: str, session=requests, params=None):
    r = session.get(url, params=params)
    r.raise_for_status()
    # print(r.url)
    time.sleep(0.5)
    return r.json()


def fetch_all_json_items(api_url, params: dict | None = None):
    all_items = []
    page = 1
    page_size = 50
    params = params if params is not None else {}
    params["maxResults"] = page_size
    while True:
        params["start"] = str(page_size * (page - 1))
        items = fetch_json(api_url, params=params)["items"]
        if not items:
            return all_items
        all_items.extend(items)
        page += 1


def fetch_totalcount(api_url, params: dict | None = None) -> int:
    params = params if params is not None else {}
    params["maxResults"] = 1
    params["getTotalCount"] = True
    totalcount = fetch_json(api_url, params=params)["totalCount"]
    return int(totalcount)

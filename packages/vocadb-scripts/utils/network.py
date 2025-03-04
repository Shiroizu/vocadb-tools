import time

import requests


def fetch_json(url: str, session=requests, params=None):
    r = session.get(url, params=params)
    r.raise_for_status()
    # print(r.url)
    time.sleep(0.5)
    return r.json()


def fetch_all_json_items(api_url, extra_params: dict | None = None):
    all_items = []
    page = 1
    page_size = 50
    extra_params = extra_params if extra_params is not None else {}
    extra_params["maxResults"] = page_size
    while True:
        extra_params["start"] = str(page_size * (page - 1))
        items = fetch_json(api_url, params=extra_params)["items"]
        if not items:
            return all_items
        all_items.extend(items)
        page += 1

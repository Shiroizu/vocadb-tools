from urllib import parse

from vdbpy.utils.network import fetch_json


def get_nico_videos_by_tag(tag: str, page=0, limit=0, min_views=0) -> list:
    nico_api = (
        "https://snapshot.search.nicovideo.jp/api/v2/snapshot/video/contents/search"
    )
    page_size = 50
    fields = "title,contentId,viewCounter,tags"

    all_videos = []

    # docs https://site.nicovideo.jp/search-api-docs/snapshot
    while True:
        options = {
            "q": parse.unquote(tag),
            "targets": "tagsExact",
            "fields": fields,
            "_limit": page_size,
            "_sort": parse.unquote("+startTime"),
            "_context": "eventchecker",
            "_offset": page * page_size,
        }

        if min_views:
            options["filters[viewCounter][gte]"] = min_views

        videos = fetch_json(nico_api, params=options)["data"]
        if not videos:
            break

        all_videos.extend(videos)

        if limit and len(all_videos) >= limit:
            return all_videos[:limit]

        page += 1

    return all_videos

from urllib import parse

from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json, fetch_text

logger = get_logger()


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


def get_viewcount(video_id: str) -> int:
    nicourl = "http://ext.nicovideo.jp/api/getthumbinfo/" + video_id
    data = fetch_text(nicourl)

    try:
        return int(data.split("<view_counter>")[1].split("</view_counter>")[0])
    except (IndexError, ValueError):
        logger.warning(f"Nico PV {video_id} deleted!")
        return 0

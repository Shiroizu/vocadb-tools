from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.network import fetch_json


@cache_with_expiration(days=4)
def get_viewcount(video_id: str, api_key: str) -> int:
    yt_base_url = "https://www.googleapis.com/youtube/v3/videos"
    url = f"{yt_base_url}?part=statistics&id={video_id}&key={api_key}"
    data = fetch_json(url)
    if not data["items"]:
        return 0
    return int(data["items"][0]["statistics"]["viewCount"])

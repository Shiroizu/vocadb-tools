from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json

logger = get_logger()


@cache_with_expiration(days=4)
def get_viewcount(video_id: str, api_key: str) -> int:
    if not api_key:
        raise ValueError("API key required for Youtube API.")
    yt_base_url = "https://www.googleapis.com/youtube/v3/videos"
    url = f"{yt_base_url}?part=statistics&id={video_id}&key={api_key}"
    data = fetch_json(url)
    if not data["items"]:
        return 0
    if "viewCount" not in data["items"][0]["statistics"]:
        logger.warning(
            f"Couldn't get viewcount for YT video '{video_id}'. Members-only?"
        )
        return 0
    return int(data["items"][0]["statistics"]["viewCount"])

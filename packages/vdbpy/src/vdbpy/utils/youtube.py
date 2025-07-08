from vdbpy.utils.network import fetch_json


def get_viewcount(video_id: str, api_key: str) -> int:
    yt_base_url = "https://www.googleapis.com/youtube/v3/videos"
    url = f"{yt_base_url}?part=statistics&id={video_id}&key={api_key}"
    data = fetch_json(url)
    return int(data["items"][0]["statistics"]["viewCount"])

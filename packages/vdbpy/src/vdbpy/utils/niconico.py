from pathlib import Path

from vdbpy.types.niconico import NicoVideo
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.date import parse_date
from vdbpy.utils.files import get_lines
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json, fetch_text

logger = get_logger()


def get_nico_videos_by_tag(
    tag_name: str,
) -> list[NicoVideo]:
    # docs: https://site.nicovideo.jp/search-api-docs/snapshot
    nico_tag_base_url = "https://www.nicovideo.jp/tag/"
    url = "https://snapshot.search.nicovideo.jp/api/v2/snapshot/video/contents/search"
    page = 0
    page_size = 32
    params = {
        "q": tag_name,
        "targets": "tagsExact",
        "_sort": "-startTime",
        "fields": "contentId,title,viewCounter,mylistCounter,likeCounter,startTime",
        "_limit": page_size,
        "_context": "vdbpy_get_nico_videos_by_tag",
    }

    videos_to_return: list[NicoVideo] = []

    logger.info(f"Fetching nico videos from url {nico_tag_base_url}{tag_name}")
    while True:
        params["_offset"] = page * page_size
        videos = fetch_json(url=url, params=params)["data"]
        if not videos:
            logger.debug("End of tag reached.")
            break
        logger.info(f"- Found {len(videos)} videos on page {page + 1}")

        for video in videos:
            video_id = video["contentId"]
            video_title = video["title"]
            view_count = video["viewCounter"]
            mylist_count = video["mylistCounter"]
            like_count = video["likeCounter"]
            publish_date = parse_date(video["startTime"])
            videos_to_return.append(
                NicoVideo(
                    id=video_id,
                    title=video_title,
                    publish_date=publish_date,
                    view_count=view_count,
                    like_count=like_count,
                    mylist_count=mylist_count,
                )
            )

        page += 1

    return videos_to_return


def get_nico_videos_by_tag_or_file(
    tag: str, file: Path, delimiter: str = "<*>"
) -> list[NicoVideo]:
    nico_videos: list[NicoVideo] = []
    if Path.is_file(file):
        lines = get_lines(file)
        for line in lines:
            if not line.strip():
                continue
            nico_id, name, publish_date_str, view_count, like_count, mylist_count = (
                line.split(delimiter)
            )
            nico_videos.append(
                NicoVideo(
                    id=nico_id,
                    title=name,
                    publish_date=parse_date(publish_date_str),
                    view_count=int(view_count),
                    like_count=int(like_count),
                    mylist_count=int(mylist_count),
                )
            )
        if nico_videos:
            logger.info(f"Existing file {file} found, parsed {len(nico_videos)} lines.")
            return nico_videos

    videos = get_nico_videos_by_tag(tag)
    logger.info(f"Found total of {len(videos)} videos.")
    if videos:
        lines = [
            f"{video.id}{delimiter}{video.title}{delimiter}{video.publish_date}{delimiter}{video.view_count}{delimiter}{video.like_count}{delimiter}{video.mylist_count}"
            for video in videos
        ]
        with Path.open(file, "w") as f:
            f.write("\n".join(lines))
            logger.info(f"Saved nico videos to {file}.")
        return videos

    logger.warning("No videos found!")
    return []


@cache_with_expiration(days=1)
def get_viewcount_1d(video_id: str, api_key: str = "") -> int:  # noqa: ARG001
    nicourl = "http://ext.nicovideo.jp/api/getthumbinfo/" + video_id
    data = fetch_text(nicourl)

    try:
        return int(data.split("<view_counter>")[1].split("</view_counter>")[0])
    except (IndexError, ValueError):
        logger.warning(f"Nico PV {video_id} deleted!")
        return 0

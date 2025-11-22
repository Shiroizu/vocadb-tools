import json
from pathlib import Path
from typing import Any

import requests

from vdbpy.api.search import get_vocalists_ids
from vdbpy.config import SONG_API_URL
from vdbpy.types.niconico import NicoVideo
from vdbpy.utils.data import get_name_language
from vdbpy.utils.logger import get_logger

logger = get_logger()


def create_song_entry(
    session: requests.Session, data: dict[Any, Any], prompt: bool = True
) -> int:
    logger.debug(f"Creating song entry with data {data}")
    if prompt:
        _ = input("Press enter to continue...")
    request_save = session.post(SONG_API_URL, {"contract": json.dumps(data)})
    request_save.raise_for_status()
    return request_save.json()


def create_song_entry_for_nico_video(
    session: requests.Session,
    video: NicoVideo,
    producer_id: int,
    vocalist_mapping: dict[str, int],
    vocalist_mapping_file: Path,
    prompt: bool = True,
) -> int:
    if video.title.count("/") != 1:
        logger.warning("Malformatted title?")
        song_name = input("Song name: ").strip()
        vocalist_line = input("Vocalist names, separated by a comma: ")
    else:
        song_name = video.title.split("/")[0].strip()
        vocalist_line = video.title.split("/")[1].strip()

    name_language = get_name_language(song_name)
    logger.info(f" Song name: '{song_name}' ({name_language})")
    vocalist_ids = get_vocalists_ids(
        vocalist_line, vocalist_mapping, vocalist_mapping_file
    )
    artist_ids: list[int] = [producer_id, *vocalist_ids]
    logger.info(f" Artist ids: {artist_ids}")

    data: dict[Any, Any] = {
        "artists": [{"artist": {"id": vocalist_id}} for vocalist_id in artist_ids],
        "draft": False,
        "names": [{"language": name_language, "value": song_name}],
        "pvUrls": [f"https://www.nicovideo.jp/watch/{video.id}"],
        "reprintPVUrl": "",
        "songType": "Original",
    }

    return create_song_entry(session, data, prompt)

import json
import time
from typing import Any

import requests

from vdbpy.config import ARTIST_API_URL
from vdbpy.types.artists import ArtistType
from vdbpy.utils.data import get_name_language
from vdbpy.utils.logger import get_logger

logger = get_logger()


def create_artist_entry(
    session: requests.Session,
    artist_name: str,
    artist_type: ArtistType,
    link: str,
    prompt: bool = True,
) -> int:
    name_language = get_name_language(artist_name)
    data: dict[Any, Any] = {
        "artistType": artist_type,
        "description": "",
        "draft": False,
        "names": [{"language": name_language, "value": artist_name}],
        "webLink": {
            "id": 0,
            "description": "NND Account",
            "url": link,
            "category": "Official",
            "disabled": False,
        },
    }
    logger.debug(f"Creating artist entry with data {data}")
    if prompt:
        _ = input("Press enter to continue...")
    request_save = session.post(ARTIST_API_URL, {"contract": json.dumps(data)})
    time.sleep(1)
    request_save.raise_for_status()
    return request_save.json()

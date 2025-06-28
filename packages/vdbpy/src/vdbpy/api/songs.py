import json
import time

from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json, fetch_json_items

logger = get_logger()


SONG_API_URL = f"{WEBSITE}/api/songs"


def get_songs(params):
    return fetch_json_items(SONG_API_URL, params=params)


def get_songs_by_artist(artist_id: int, params: dict):
    params["artistId[]"] = artist_id
    return fetch_json_items(SONG_API_URL, params)


def get_songs_by_tag(tag_id: int, params: dict):
    params["tagId[]"] = tag_id
    return fetch_json_items(SONG_API_URL, params)


def add_event(session, song_id: int, event_id: int, update_note) -> bool:
    logger.debug(f"Adding event {event_id} to song {song_id} ({update_note}).")
    entry_data = session.get(f"{WEBSITE}/api/songs/{song_id}/for-edit").json()
    entry_event_ids = [event["id"] for event in entry_data["releaseEvents"]]
    if event_id in entry_event_ids:
        logger.warning("Event already added to the entry.")
        return False

    entry_data["releaseEvents"].append({"id": event_id})
    entry_data["updateNotes"] = update_note

    request_save = session.post(
        f"{WEBSITE}/api/songs/{song_id}", {"contract": json.dumps(entry_data)}
    )

    request_save.raise_for_status()
    time.sleep(1)
    return True

def get_by_pv(pv_service: str, pv_id: str):
    url = f"{WEBSITE}/api/songs/byPv"
    return fetch_json(
        url,
        params={
            "pvService": pv_service,
            "fields": "ReleaseEvent",
            "pvId": pv_id,
        },
    )

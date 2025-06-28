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

def mark_pvs_unavailable(session, song_id: int, service=""):
    """Mark all original PVs as unavailable in a song entry.

    Does not do an extra check if the PV is unavailable or not!
    """
    logger.info(f"Marking all original PVs unavailable for song {song_id}.")
    if service:
        logger.info(f"Restricting to PV service {service}")
    entry_data = session.get(f"{WEBSITE}/api/songs/{song_id}/for-edit").json()
    # 'pvs': [{
    #   'author': '染井 吉野',
    #   'disabled': False,
    #   'id': 1137552,
    #   'length': 118,
    #   'name': 'LastDay light 花隈千冬 小春六花',
    #   'publishDate': '2025-02-22T00:00:00',
    #   'pvId': 'Xe0f8K-i6HE',
    #   'service': 'Youtube',
    #   'pvType': 'Original',
    #   'thumbUrl': 'https://i.ytimg.com/vi/Xe0f8K-i6HE/default.jpg',
    #   'url': 'https://youtu.be/Xe0f8K-i6HE'
    # }]
    updated_pv_urls = []
    for pv in entry_data["pvs"]:
        logger.debug(f"{pv['pvId']} {pv['service']} ({pv['pvType']})")
        if pv["pvType"] != "Original":
            logger.debug("Not original, skipping.")
            continue

        if pv["disabled"]:
            logger.debug("PV is already disabled.")
            continue

        if service and service != pv["service"]:
            logger.debug("Skipping service.")
            continue

        updated_pv_urls.append(pv["url"])
        pv["disabled"] = True

    if updated_pv_urls:
        update_note = "Marked PVs as unavailable: "
        update_note += ", ".join(updated_pv_urls)
        logger.info(update_note)
        entry_data["updateNotes"] = update_note

        request_save = session.post(
            f"{WEBSITE}/api/songs/{song_id}",
            {"contract": json.dumps(entry_data)},
        )
        request_save.raise_for_status()
        time.sleep(2)

    else:
        logger.info(f"No PV links to update for song {song_id}")

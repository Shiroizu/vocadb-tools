import json
import random
import time
from typing import Callable

from vdbpy.config import WEBSITE
from vdbpy.types import Service
from vdbpy.utils import niconico, youtube
from vdbpy.utils.cache import cache_without_expiration
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount, fetch_json, fetch_json_items

logger = get_logger()


SONG_API_URL = f"{WEBSITE}/api/songs"


def get_songs(params):
    return fetch_json_items(SONG_API_URL, params=params)


def get_song_by_id(song_id, fields=""):
    params = {"fields": fields} if fields else {}
    url = f"{SONG_API_URL}/{song_id}"
    return fetch_json(url, params=params)


def get_songs_by_artist_id(artist_id: int, params: dict):
    params["artistId[]"] = artist_id
    return fetch_json_items(SONG_API_URL, params)


def get_songs_by_tag_id(tag_id: int, params: dict):
    params["tagId[]"] = tag_id
    return fetch_json_items(SONG_API_URL, params)


def add_event_to_song(session, song_id: int, event_id: int, update_note) -> bool:
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


def get_song_entry_by_pv(pv_service: str, pv_id: str):
    url = f"{WEBSITE}/api/songs/byPv"
    return fetch_json(
        url,
        params={
            "pvService": pv_service,
            "fields": "ReleaseEvent",
            "pvId": pv_id,
        },
    )


def mark_pvs_unavailable_by_song_id(session, song_id: int, service=""):
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


def get_random_rated_song_by_user(user: tuple[str, int]) -> int:
    url = f"{WEBSITE}/api/songs"
    username, user_id = user
    params = {
        "userCollectionId": user_id,
        "onlyWithPVs": True,
        "maxResults": 1,
    }
    total = fetch_cached_totalcount(url, params=params)
    if not total:
        logger.warning(f"No rated songs with PVs found for user {username} ({user_id})")
        return 0

    random_start = random.randint(0, total - 1)
    logger.debug(f"Selecting random_start {random_start}")
    params["start"] = random_start
    return fetch_json(url, params=params)["items"][0]["id"]


def get_related_songs_by_song_id(song_id: int):
    url = f"{WEBSITE}/api/songs/{song_id}/related"
    return fetch_json(url)


def get_random_related_song_by_song_id(song_id: int) -> int:
    logger.debug(f"Fetching related songs for S/{song_id}")
    related_songs = get_related_songs_by_song_id(song_id)
    columns = ["artistMatches", "likeMatches", "tagMatches"]
    selected_column = random.choice(columns)
    logger.debug(f"Selecting random related song from {selected_column}")
    if selected_column not in related_songs or not related_songs[selected_column]:  # type: ignore
        logger.warning(f"No related songs found in {selected_column} for S/{song_id}.")
        return 0
    selected_entry = random.choice(related_songs[selected_column])  # type: ignore
    return selected_entry["id"]


def get_random_song_id() -> int:
    url = f"{WEBSITE}/api/songs"
    params = {
        "getTotalCount": True,
        "onlyWithPVs": True,
        "maxResults": 1,
    }
    total = fetch_cached_totalcount(url, params=params)

    random_start = random.randint(0, total - 1)
    logger.debug(f"Selecting random_start {random_start}")
    params["start"] = random_start
    return fetch_json(url, params=params)["items"][0]["id"]


def get_song_rater_ids_by_song_id(song_id: int, session=None) -> list[int]:
    """Fetch the IDs of users who rated a song."""
    url = f"{WEBSITE}/api/songs/{song_id}/ratings"
    """
    [
    {
        "date": "2015-07-09T14:07:23.91",
        "user": {
            "active": true,
            "groupId": "Regular",
            "memberSince": "2011-10-31T23:55:36",
            "verifiedArtist": false,
            "id": 45,
            "name": "gaminat"
        },
        "rating": "Favorite"
    }, ...
    """

    raters = fetch_json(url, session=session) if session else fetch_json(url)
    rater_ids = [rater["user"]["id"] for rater in raters if "user" in rater]
    logger.debug(f"Found {len(rater_ids)} rater IDs for song {song_id}: {rater_ids}")
    return rater_ids


def get_viewcounts_by_song_id_and_service(
    song_id: int, service: Service, api_keys: dict[Service, str]
) -> list[tuple[str, str, int]]:
    # Returns a tuple of (pv_url, pv_type, viewcount)
    pvs = get_song_by_id(song_id, fields="pvs")["pvs"]
    # [{"author":"ミナツキトーカ","disabled":false,"id":197272,"length":274,"name":"- moonlight waltz -　月夜の舞踏譜 【波音リツ・重音テト オリジナル】","publishDate":"2016-10-12T00:00:00","pvId":"sm29822681","service":"NicoNicoDouga","pvType":"Original","thumbUrl":"https://nicovideo.cdn.nimg.jp/thumbnails/29822681/29822681","url":"http://www.nicovideo.jp/watch/sm29822681"}, ...]
    viewcount_functions: dict[Service, Callable[..., int]] = {
        "NicoNicoDouga": niconico.get_viewcount,
        "Youtube": youtube.get_viewcount,
    }
    return [
        (
            pv["url"],
            pv["pvType"],
            viewcount_functions[pv["service"]](pv["pvId"], api_keys.get(pv["service"])),
        )
        for pv in pvs
        if pv["service"] == service and not pv["disabled"]
    ]


@cache_without_expiration()
def get_entry_creator_id_by_song_id(song_id: int) -> int:
    url = f"{WEBSITE}/api/songs/versions/{song_id}"
    return fetch_json(url)["archivedVersions"][-1]["author"]["id"]


def get_songlist_author_ids_by_song_id(song_id: int) -> list[int]:
    # [{"author":{...},"canEdit":true,"deleted":false,"description":"...","status":"Finished","thumb":{"entryType":"SongList","id":186,"mime":"image/png","version":294},"version":294,"featuredCategory":"Pools","id":186,"name":"(NND) More than 100K views"}, ...]
    url = f"{WEBSITE}/api/songs/{song_id}/songlists"
    songlists = fetch_json(url)
    return [songlist["author"]["id"] for songlist in songlists]

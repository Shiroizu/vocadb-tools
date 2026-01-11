import random
from typing import Any

import requests

from vdbpy.api.edits import get_edits_by_entry
from vdbpy.config import SONG_API_URL, SONGLIST_API_URL
from vdbpy.parsers.songs import parse_song
from vdbpy.types.shared import (
    Service,
)
from vdbpy.types.songs import (
    OptionalSongFieldName,
    SongEntry,
    SongSearchParams,
)
from vdbpy.types.users import User
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_json,
    fetch_json_items,
    fetch_json_items_with_total_count,
    fetch_total_count_30d,
)

logger = get_logger()


def get_json_songs_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[dict[Any, Any]], int]:
    return fetch_json_items_with_total_count(
        SONG_API_URL, params=params, max_results=max_results
    )


def get_songs_with_total_count(
    fields: set[OptionalSongFieldName] | None = None,
    song_search_params: SongSearchParams | None = None,
) -> tuple[list[SongEntry], int]:
    params: dict[str, str | int | list[str]] = {}

    logger.debug("Fetching songs with total count:")
    logger.debug(f"Got song search params {song_search_params}")
    logger.debug(f"Got fields {fields}")

    if fields:
        params["fields"] = ",".join(fields)

    if song_search_params:
        # Verify search param usage
        # TODO dry
        if song_search_params.unify_types_and_tags and not song_search_params.tag_ids:
            msg = "Search filter 'unify_types_and_tags'"
            msg += " requires song type tags to be present."
            raise ValueError(msg)
        if (
            song_search_params.artist_participation_status
            and not song_search_params.artist_ids
        ):
            msg = "Search filter 'artist_participation_status'"
            msg += " requires artist ids to be present."
            raise ValueError(msg)
        if (
            song_search_params.include_child_voicebanks
            and not song_search_params.artist_ids
        ):
            msg = "Search filter 'include_child_voicebanks'"
            msg += " requires artist ids to be present."
            raise ValueError(msg)
        if song_search_params.include_child_tags and not song_search_params.tag_ids:
            msg = "Search filter 'include_child_tags'"
            msg += " requires tag ids to be present."
            raise ValueError(msg)
        if (
            song_search_params.include_group_members
            and not song_search_params.artist_ids
        ):
            msg = "Search filter 'include_group_members'"
            msg += " requires artist ids to be present."
            raise ValueError(msg)
        params.update(song_search_params.to_url_params())

    logger.debug(f"Query parameters: {params}")

    songs_to_parse, total_count = fetch_json_items_with_total_count(
        SONG_API_URL, params=params
    )
    logger.debug(f"Found {len(songs_to_parse)} songs to parse")

    return [parse_song(song, fields) for song in songs_to_parse], total_count


def get_songs(
    song_search_params: SongSearchParams | None = None,
    fields: set[OptionalSongFieldName] | None = None,
) -> list[SongEntry]:
    return get_songs_with_total_count(fields, song_search_params)[0]


def get_song_by_id(
    song_id: int, fields: set[OptionalSongFieldName] | None = None
) -> SongEntry:
    url = f"{SONG_API_URL}/{song_id}"
    params = {"fields": ",".join(fields)} if fields else {}
    return parse_song(fetch_json(url, params=params), fields=fields)


@cache_without_expiration()
def get_cached_song_by_entry_id_and_version_id(
    song_id: int, version_id: int, fields: set[OptionalSongFieldName] | None = None
) -> SongEntry | None:
    logger.debug(
        f"Fetching cached song by entry id {song_id} and version id {version_id}..."
    )

    most_recent_edit = get_edits_by_entry("Song", song_id, include_deleted=True)[0]
    if most_recent_edit.version_id != version_id:
        logger.warning(
            f"    Cached entry has been edited after v{version_id}. Not going to fetch."
        )
        return None

    # TODO cacheable type for optional song fields
    uncacheable_fields: set[OptionalSongFieldName] = {"albums", "tags"}
    if fields:
        field_intersection = fields & uncacheable_fields
        if field_intersection:
            msg = f"Cannot fetch cached song including field {field_intersection}"
            raise ValueError(msg)
    return get_song_by_id(song_id, fields=fields)


def get_song_by_pv(
    pv_service: Service, pv_id: str, fields: set[OptionalSongFieldName] | None = None
) -> SongEntry | None:
    params = {
        "pvService": pv_service,
        "pvId": pv_id,
    }
    if fields:
        params["fields"] = ",".join(fields)
    entry = fetch_json(f"{SONG_API_URL}/byPv", params=params)
    return parse_song(entry, fields=fields) if entry else None


def get_tag_voters_by_song_id_and_tag_ids(
    song_id: int, tag_ids: list[int], session: requests.Session
) -> dict[int, list[User]]:
    # TODO generic entry get tag voters
    url = f"{SONG_API_URL}/{song_id}/tagUsages"
    tag_votes: dict[int, list[Any]] = {}
    taggings = fetch_json(url, session=session)
    if "tagUsages" not in taggings:
        logger.info(f"Tags not found for S/{song_id}")
        return tag_votes
    for tagging in taggings["tagUsages"]:
        tag_id = tagging["tag"]["id"]
        if tag_id in tag_ids:
            tag_votes[tag_id] = tagging["votes"]
    return tag_votes


def get_random_rated_song_id_by_user(user: tuple[str, int]) -> int:
    username, user_id = user
    params = {
        "userCollectionId": user_id,
        "onlyWithPVs": True,
        "maxResults": 1,
    }
    total = fetch_total_count_30d(SONG_API_URL, params=params)
    if not total:
        logger.warning(f"No rated songs with PVs found for user {username} ({user_id})")
        return 0
    random_start = random.randint(0, total - 1)
    logger.debug(f"Selecting random_start {random_start}")
    params["start"] = random_start
    return fetch_json(SONG_API_URL, params=params)["items"][0]["id"]


def get_related_songs_by_song_id(song_id: int) -> dict[Any, Any]:
    # TODO type:
    url = f"{SONG_API_URL}/{song_id}/related"
    return fetch_json(url)


def get_random_related_song_id_by_song_id(song_id: int) -> int:
    logger.debug(f"Fetching related songs for S/{song_id}")
    related_songs = get_related_songs_by_song_id(song_id)
    columns = ["artistMatches", "likeMatches", "tagMatches"]
    selected_column = random.choice(columns)
    logger.debug(f"Selecting random related song from {selected_column}")
    if selected_column not in related_songs or not related_songs[selected_column]:
        logger.warning(f"No related songs found in {selected_column} for S/{song_id}.")
        return 0
    selected_entry = random.choice(related_songs[selected_column])
    return selected_entry["id"]


def get_random_song_id(song_search_params: SongSearchParams | None = None) -> int:
    params = song_search_params if song_search_params else SongSearchParams()
    params.max_results = 1
    _, total = get_songs_with_total_count(song_search_params=params)
    random_start = random.randint(0, total - 1)
    logger.debug(f"Selecting random_start {random_start}")
    params.start = random_start
    return get_songs(song_search_params=params)[0].id


def get_song_rater_ids_by_song_id(
    song_id: int, session: requests.Session | None = None
) -> list[int]:
    """Fetch the IDs of users who rated a song."""
    url = f"{SONG_API_URL}/{song_id}/ratings"
    raters = fetch_json(url, session=session) if session else fetch_json(url)
    rater_ids = [rater["user"]["id"] for rater in raters if "user" in rater]
    logger.debug(f"Found {len(rater_ids)} rater IDs for song {song_id}: {rater_ids}")
    return rater_ids


# TODO fix
# def get_viewcounts_by_song_id_and_service(
#     song_id: int,
#     service: Service,
#     api_keys: dict[Service, str],
#     precalculated_data: dict[str, int] | None,
# ) -> list[tuple[str, PvType, int]]:
#     # Returns a tuple of (pv_url, pv_type, viewcount)
#     pvs = get_song_by_id(song_id, fields={"pvs"}).pvs
#     if precalculated_data is None:
#         precalculated_data = {}
#     viewcount_functions: dict[Service, Callable[..., int]] = {
#         "NicoNicoDouga": niconico.get_viewcount_1d,
#         "Youtube": youtube.get_viewcount_1d,
#     }
#     new_data: list[tuple[str, str, int]] = []
#     for pv in pvs:
#         if pv["service"] == service and not pv["disabled"]:
#             if pv["pvId"] in precalculated_data:
#                 new_viewcount = precalculated_data[pv["pvId"]]
#             else:
#                 new_viewcount = viewcount_functions[pv["service"]](
#                     pv["pvId"], api_keys.get(pv["service"])
#                 )
#             new_data.append((pv["url"], pv["pvType"], new_viewcount))
#     return new_data


@cache_without_expiration()
def get_cached_entry_creator_id_by_song_id(song_id: int) -> int:
    # TODO generic get_entry_creator
    url = f"{SONG_API_URL}/{song_id}/versions"
    return fetch_json(url)["archivedVersions"][-1]["author"]["id"]


def get_songlist_author_ids_by_song_id(song_id: int) -> list[int]:
    url = f"{SONG_API_URL}/{song_id}/songlists"
    songlists = fetch_json(url)
    return [songlist["author"]["id"] for songlist in songlists]


def get_relevant_user_ids_by_song_id(
    song_id: int, session: requests.Session | None = None
) -> list[int]:
    song_raters = get_song_rater_ids_by_song_id(song_id, session)
    entry_creator = get_cached_entry_creator_id_by_song_id(song_id)
    songlist_authors = get_songlist_author_ids_by_song_id(song_id)
    return list({*song_raters, entry_creator, *songlist_authors})


@cache_with_expiration(days=1)
def get_most_rated_song_by_artist_id_1d(
    artist_id: int,
) -> SongEntry:
    return get_songs(
        song_search_params=SongSearchParams(
            max_results=1, artist_ids={artist_id}, sort="RatingScore"
        )
    )[0]


@cache_with_expiration(days=1)
def get_most_recent_song_by_artist_id_1d(artist_id: int) -> SongEntry:
    return get_songs(
        song_search_params=SongSearchParams(
            max_results=1, artist_ids={artist_id}, sort="PublishDate"
        )
    )[0]


# ---------------------------------------------- #


def get_song_entries_by_songlist_id(
    songlist_id: int, params: dict[Any, Any] | None = None
) -> list[dict[Any, Any]]:
    # TODO fix return type
    params = {} if params is None else params
    url = f"{SONGLIST_API_URL}/{songlist_id}/songs"
    return fetch_json_items(url, params=params)


@cache_with_expiration(days=7)
def get_rated_songs_by_user_id_7d(
    user_id: int, fields: set[OptionalSongFieldName] | None = None
) -> list[SongEntry]:
    logger.info(f"Fetching rated songs for user id {user_id}")
    rated_songs = get_songs(
        song_search_params=SongSearchParams(
            user_collection_id=user_id,
        ),
        fields=fields,
    )
    logger.info(f"Found total of {len(rated_songs)} rated songs.")
    return rated_songs

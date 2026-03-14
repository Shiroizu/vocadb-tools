"""User library cache for rated songs, albums, and followed artists.

Stores a per-user gzip-compressed JSON file so that downstream consumers
(favourite_x scripts, TetoBot commands) share a single cached dataset.

Refresh strategy (per collection):
1. Fetch current total count (cheap maxResults=1 call).
2. If count unchanged --> skip entirely.
3. If count changed:
   - Rated songs: fetch diff+1 items (sort=RatingDate), validate last_id, then
     either incremental merge or full rebuild.
   - Albums / followed artists: full rebuild only. The API does not support
     sort=CollectionDate or sort=FollowDate (AdditionDate is entry creation),
     so incremental update is not reliable: https://github.com/VocaDB/vocadb/issues/2133

Known edge case (rated songs): re-rating a song doesn't change the count and
will be missed. Delete the cache file or call get_user_library(force_refresh=True).
"""

import gzip
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from vdbpy.api.albums import get_albums_by_user_id
from vdbpy.api.artists import get_followed_artists_by_user_id
from vdbpy.api.songs import get_rated_songs_with_ratings
from vdbpy.config import USER_API_URL
from vdbpy.types.songs import OptionalSongFieldName
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_total_count

logger = get_logger()

RATED_SONG_FIELDS: set[OptionalSongFieldName] = {
    "albums",
    "artists",
    "tags",
    "cultureCodes",
}


# -------------------- types -------------------- #


@dataclass
class RatedSongEntry:
    song: dict[str, Any]
    rating: str  # "Favorite" | "Like"
    date: str = ""  # ISO 8601 rating date


@dataclass
class UserLibrary:
    user_id: int
    rated_songs: dict[int, RatedSongEntry] = field(default_factory=dict)
    albums: list[dict[str, Any]] = field(default_factory=list)
    followed_artists: list[dict[str, Any]] = field(default_factory=list)
    rated_songs_count: int = 0
    rated_songs_last_id: int = 0
    albums_count: int = 0
    albums_last_id: int = 0
    followed_artists_count: int = 0
    followed_artists_last_id: int = 0


# -------------------- cache I/O -------------------- #


def _get_library_dir() -> Path:
    cache_dir = Path.home() / ".cache"
    if not cache_dir.is_dir():
        cache_dir = Path.cwd() / "cache"
    library_dir = cache_dir / "vdb" / "user_library"
    website_env = os.environ.get("VDBPY_WEBSITE", "").rstrip("/")
    if website_env:
        library_dir = library_dir / urlparse(website_env).netloc
    library_dir.mkdir(exist_ok=True, parents=True)
    return library_dir


def get_library_path(user_id: int) -> Path:
    return _get_library_dir() / f"{user_id}.json.gz"


def _load_library_cache(user_id: int) -> UserLibrary:
    path = get_library_path(user_id)
    if not path.exists():
        return UserLibrary(user_id=user_id)
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        rated_songs = {
            int(song_id): RatedSongEntry(
                song=v["song"], rating=v["rating"], date=v.get("date", "")
            )
            for song_id, v in data.get("rated_songs", {}).items()
        }
        return UserLibrary(
            user_id=user_id,
            rated_songs=rated_songs,
            albums=data.get("albums", []),
            followed_artists=data.get("followed_artists", []),
            rated_songs_count=data.get("rated_songs_count", 0),
            rated_songs_last_id=data.get("rated_songs_last_id", 0),
            albums_count=data.get("albums_count", 0),
            albums_last_id=data.get("albums_last_id", 0),
            followed_artists_count=data.get("followed_artists_count", 0),
            followed_artists_last_id=data.get("followed_artists_last_id", 0),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to load library cache for user {user_id}: {e}")
        return UserLibrary(user_id=user_id)


def _save_library_cache(user_id: int, lib: UserLibrary) -> None:
    path = get_library_path(user_id)
    data: dict[str, Any] = {
        "user_id": user_id,
        "rated_songs_count": lib.rated_songs_count,
        "rated_songs_last_id": lib.rated_songs_last_id,
        "albums_count": lib.albums_count,
        "albums_last_id": lib.albums_last_id,
        "followed_artists_count": lib.followed_artists_count,
        "followed_artists_last_id": lib.followed_artists_last_id,
        "rated_songs": {
            str(song_id): {
                "song": entry.song,
                "rating": entry.rating,
                "date": entry.date,
            }
            for song_id, entry in lib.rated_songs.items()
        },
        "albums": lib.albums,
        "followed_artists": lib.followed_artists,
    }
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.debug(f"Saved library cache for user {user_id} to {path}")


# -------------------- refresh helpers -------------------- #


def _update_rated_songs(
    lib: UserLibrary,
    current_count: int,
    force: bool,
    session: requests.Session | None = None,
) -> None:
    diff = current_count - lib.rated_songs_count
    can_increment = not force and diff > 0 and lib.rated_songs_count > 0

    if can_increment:
        entries = get_rated_songs_with_ratings(
            lib.user_id,
            fields=RATED_SONG_FIELDS,
            max_results=diff + 1,
            session=session,
        )
        last_id_matches = entries[diff]["song"]["id"] == lib.rated_songs_last_id
        if len(entries) > diff and last_id_matches:
            logger.info(
                f"Incremental rated songs update for user {lib.user_id}: +{diff} songs"
            )
            for entry in entries[:diff]:
                lib.rated_songs[entry["song"]["id"]] = RatedSongEntry(
                    song=entry["song"],
                    rating=entry["rating"],
                    date=entry.get("date", ""),
                )
            lib.rated_songs_last_id = entries[0]["song"]["id"]
            lib.rated_songs_count = current_count
            return
        logger.info(
            f"Rated songs n+1 check failed for user {lib.user_id}, doing full rebuild"
        )

    logger.info(
        f"Full rated songs rebuild for user {lib.user_id} "
        f"(cached={lib.rated_songs_count}, current={current_count})"
    )
    entries = get_rated_songs_with_ratings(
        lib.user_id, fields=RATED_SONG_FIELDS, session=session
    )
    lib.rated_songs = {
        e["song"]["id"]: RatedSongEntry(
            song=e["song"], rating=e["rating"], date=e.get("date", "")
        )
        for e in entries
    }
    lib.rated_songs_last_id = entries[0]["song"]["id"] if entries else 0
    lib.rated_songs_count = current_count
    logger.info(f"Rebuilt {len(lib.rated_songs)} rated songs for user {lib.user_id}")


def _update_albums(
    lib: UserLibrary,
    current_count: int,
    _force: bool,
    session: requests.Session | None = None,
) -> None:
    """Full rebuild only; API has no sort=CollectionDate, incremental unreliable."""
    logger.info(
        f"Full albums rebuild for user {lib.user_id} "
        f"(cached={lib.albums_count}, current={current_count})"
    )
    lib.albums = get_albums_by_user_id(
        lib.user_id,
        extra_params={"fields": "Artists"},
        session=session,
    )
    lib.albums_last_id = lib.albums[0]["album"]["id"] if lib.albums else 0
    lib.albums_count = current_count
    logger.info(f"Rebuilt {len(lib.albums)} albums for user {lib.user_id}")


def _update_followed_artists(
    lib: UserLibrary,
    current_count: int,
    _force: bool,
    session: requests.Session | None = None,
) -> None:
    """Full rebuild only; API has no sort=FollowDate, incremental unreliable."""
    logger.info(
        f"Full followed artists rebuild for user {lib.user_id} "
        f"(cached={lib.followed_artists_count}, current={current_count})"
    )
    lib.followed_artists = get_followed_artists_by_user_id(lib.user_id, session=session)
    lib.followed_artists_last_id = (
        lib.followed_artists[0]["id"] if lib.followed_artists else 0
    )
    lib.followed_artists_count = current_count
    logger.info(
        f"Rebuilt {len(lib.followed_artists)} followed artists for user {lib.user_id}"
    )


# -------------------- public API -------------------- #


ALL_COLLECTIONS: frozenset[str] = frozenset(
    {"rated_songs", "albums", "followed_artists"}
)


def get_user_library(
    user_id: int,
    force_refresh: bool = False,
    collections: frozenset[str] | None = None,
    session: requests.Session | None = None,
) -> UserLibrary:
    if collections is None:
        collections = ALL_COLLECTIONS

    lib = _load_library_cache(user_id)

    from vdbpy.api.users import (  # noqa: PLC0415
        has_public_album_collection,
        has_public_song_ratings,
    )

    if "rated_songs" in collections:
        if has_public_song_ratings(user_id, session) is False:
            logger.warning(
                f"User {user_id} has private song ratings. "
                "Skipping rated songs refresh.",
            )
        else:
            rated_count = fetch_total_count(
                f"{USER_API_URL}/{user_id}/ratedSongs",
                params={"groupByRating": False},
                session=session,
            )
            if force_refresh or rated_count != lib.rated_songs_count:
                _update_rated_songs(lib, rated_count, force_refresh, session=session)
            else:
                logger.info(
                    f"Rated songs up to date for u/{user_id} ({lib.rated_songs_count})"
                )

    if "albums" in collections:
        if not has_public_album_collection(user_id):
            logger.warning(
                f"User {user_id} has private album collection. "
                "Skipping albums refresh.",
            )
        else:
            albums_count = fetch_total_count(
                f"{USER_API_URL}/{user_id}/albums",
                params={},
                session=session,
            )
            if force_refresh or albums_count != lib.albums_count:
                _update_albums(lib, albums_count, force_refresh, session=session)
            else:
                logger.info(
                    f"Albums up to date for user {user_id} ({lib.albums_count})"
                )

    if "followed_artists" in collections:
        followed_count = fetch_total_count(
            f"{USER_API_URL}/{user_id}/followedArtists", session=session
        )
        if force_refresh or followed_count != lib.followed_artists_count:
            _update_followed_artists(
                lib, followed_count, force_refresh, session=session
            )
        else:
            logger.info(
                f"Followed artists up to date for user {user_id} "
                f"({lib.followed_artists_count})"
            )

    _save_library_cache(user_id, lib)
    return lib

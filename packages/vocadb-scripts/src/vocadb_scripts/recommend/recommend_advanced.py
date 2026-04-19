"""Build a personalised original-song recommendation songlist on VocaDB.

Uses the raw output of `find_favourite_tags` and `find_favourite_producers`.

- Linear weighting. Top 1 pick is 50x as common than top 50.
- Query originals sorted by rating score
- Pick the first unrated and unseen result

The previous songlist is deleted before the new one is created.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests
from vdbpy.api.songlists import create_or_update_songlist, delete_songlist
from vdbpy.api.songs import get_songs_with_total_count
from vdbpy.api.user_library import get_user_library
from vdbpy.api.users import find_user_by_username_1d
from vdbpy.config import WEBSITE
from vdbpy.types.songs import SongEntry, SongSearchParams
from vdbpy.utils.dump import build_tag_info_map
from vdbpy.utils.files import (
    get_credentials,
    get_lines,
    replace_line_in_file,
    save_file,
)
from vdbpy.utils.logger import get_logger

from scripts.find.favourite_producers import build_top_favourite_producers
from scripts.find.favourite_tags import build_top_favourite_genres

logger = get_logger()

LIST_LENGTH = 10
TOP_FAVOURITES = 50
PER_SLOT_MAX_RESULTS = 45
MAX_FINDER_ITERATIONS = 200
WEIGHT = 1e-9


@dataclass(frozen=True)
class SearchSignal:
    kind: str  # "tag" | "producer"
    id: int


def _default_state_dir() -> Path:
    env = os.environ.get("VOCADB_RECOMMEND_STATE_DIR", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "data" / "state"


def _seen_path(state_dir: Path) -> Path:
    return state_dir / "recommended_songs.csv"


def _last_songlist_path(state_dir: Path) -> Path:
    return state_dir / "advanced_last_songlist.json"


def _parse_seen_ids_for_user(path: Path, user_id: int) -> set[int]:
    line_start = f"{user_id},"
    for line in get_lines(path):
        if not line or not line.startswith(line_start):
            continue
        parts = line.split(",")
        return {int(s) for s in parts[1:] if s.isnumeric()}
    return set()


def get_seen_song_ids(user_id: int, state_dir: Path) -> set[int]:
    return _parse_seen_ids_for_user(_seen_path(state_dir), user_id)


def add_seen_song_ids(user_id: int, new_ids: list[int], state_dir: Path) -> None:
    existing = get_seen_song_ids(user_id, state_dir)
    all_ids = existing | set(new_ids)
    ids_str = ",".join(str(s) for s in sorted(all_ids))
    line_start = f"{user_id},"
    new_line = f"{user_id},{ids_str}"
    path = _seen_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [line for line in get_lines(path) if line]
    if any(line.startswith(line_start) for line in lines):
        replace_line_in_file(path, line_start, new_line, startswith=True)
    else:
        save_file(path, new_line, append=True)


def _load_json_object(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not load {path}: {e}")
        return {}


def _save_json_object(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _load_last_songlist_id(state_dir: Path, user_id: int) -> int | None:
    raw = _load_json_object(_last_songlist_path(state_dir))
    key = str(user_id)
    if key not in raw:
        return None
    try:
        n = int(raw[key])
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def _save_last_songlist_id(state_dir: Path, user_id: int, songlist_id: int) -> None:
    path = _last_songlist_path(state_dir)
    data = _load_json_object(path)
    data[str(user_id)] = songlist_id
    _save_json_object(path, data)


def _delete_previous_songlist(
    session: requests.Session,
    state_dir: Path,
    user_id: int,
) -> None:
    prev = _load_last_songlist_id(state_dir, user_id)
    if prev is None:
        return
    try:
        delete_songlist(session, prev)
    except requests.RequestException as e:
        logger.warning(f"Could not delete previous songlist {prev}: {e}")


def _fetch_originals_by_tag_or_artist(
    sig: SearchSignal,
    max_results: int,
    session: requests.Session | None,
) -> list[SongEntry]:
    if sig.kind == "tag":
        params = SongSearchParams(
            tag_ids={sig.id},
            song_types={"Original"},
            sort="RatingScore",
            max_results=max_results,
            only_with_pvs=True,
        )
    elif sig.kind == "producer":
        params = SongSearchParams(
            artist_ids={sig.id},
            song_types={"Original"},
            sort="RatingScore",
            max_results=max_results,
            only_with_pvs=True,
        )
    else:
        msg = f"unknown signal kind {sig.kind!r}"
        raise ValueError(msg)
    songs, total = get_songs_with_total_count(
        fields={"artists", "tags"},
        song_search_params=params,
        session=session,
    )
    logger.info(
        f"recommend_advanced: search {sig.kind} id={sig.id} -> {len(songs)} "
        f"page hits (totalCount={total})"
    )
    logger.debug(f"recommend_advanced search params: {params.to_url_params()}")
    return songs


def _first_unrated_unseen(
    songs: list[SongEntry],
    rated_song_ids: set[int],
    seen_ids: set[int],
    run_seen: set[int],
) -> SongEntry | None:
    for song in songs:
        if song.id in rated_song_ids or song.id in seen_ids or song.id in run_seen:
            continue
        return song
    return None


def _weighted_pick_row(
    rows: list[tuple[int, str, float]],
    skip: set[int],
    rng: random.Random,
) -> tuple[int, str, int] | None:
    """Pick one row by weight; return (id, name, rank_1_based in ``rows``)."""
    eligible = [r for r in rows if r[0] not in skip]
    if not eligible:
        return None

    def rank_weight(item_id: int) -> float:
        rank = next(i for i, r in enumerate(rows, start=1) if r[0] == item_id)
        return len(rows) + 1 - rank

    weights = [rank_weight(e[0]) for e in eligible]
    chosen = rng.choices(eligible, weights=weights, k=1)[0]
    rank = next(i for i, r in enumerate(rows, start=1) if r[0] == chosen[0])
    return (chosen[0], chosen[1], rank)


def _note_genre_pick(
    tag_rank: int,
    tag_id: int,
    tag_name: str,
    n_genres: int,
) -> str:
    return (
        f"Via genre tag: {tag_name} (id {tag_id}), "
        f"#{tag_rank}/{n_genres} in your top favourite genres"
    )


def _note_producer_pick(
    prod_rank: int,
    prod_id: int,
    prod_name: str,
    n_producers: int,
) -> str:
    return (
        f"Via producer search: {prod_name} (id {prod_id}), "
        f"#{prod_rank}/{n_producers} in your top favourite producers"
    )


def _collect_weighted_side(
    rows: list[tuple[int, str, float]],
    kind: str,
    want: int,
    rng: random.Random,
    rated_song_ids: set[int],
    seen_ids: set[int],
    run_seen: set[int],
    skip: set[int],
    n_genres: int,
    n_producers: int,
    session: requests.Session | None,
) -> list[tuple[SongEntry, str]]:
    if want <= 0 or not rows:
        return []

    out: list[tuple[SongEntry, str]] = []
    iterations = 0

    while len(out) < want and iterations < MAX_FINDER_ITERATIONS:
        iterations += 1
        picked = _weighted_pick_row(rows, skip, rng)
        if picked is None:
            break
        eid, ename, rank = picked
        sig = SearchSignal(kind, eid)
        songs = _fetch_originals_by_tag_or_artist(sig, PER_SLOT_MAX_RESULTS, session)
        hit = _first_unrated_unseen(songs, rated_song_ids, seen_ids, run_seen)
        if hit is not None:
            if kind == "tag":
                note = _note_genre_pick(rank, eid, ename, n_genres)
            else:
                note = _note_producer_pick(rank, eid, ename, n_producers)
            out.append((hit, note))
            run_seen.add(hit.id)
        else:
            skip.add(eid)

    return out


def _interleave(
    genre_items: list[tuple[SongEntry, str]],
    prod_items: list[tuple[SongEntry, str]],
) -> list[tuple[SongEntry, str]]:
    out: list[tuple[SongEntry, str]] = []
    n = max(len(genre_items), len(prod_items))
    for i in range(n):
        if i < len(genre_items):
            out.append(genre_items[i])
        if i < len(prod_items):
            out.append(prod_items[i])
    return out


def _select_songs_split(
    genre_rows: list[tuple[int, str, float]],
    producer_rows: list[tuple[int, str, float]],
    rated_song_ids: set[int],
    seen_ids: set[int],
    list_length: int,
    rng: random.Random,
    session: requests.Session | None,
) -> list[tuple[SongEntry, str]]:

    has_g = bool(genre_rows)
    has_p = bool(producer_rows)
    if not has_g and not has_p:
        return []

    if has_g and has_p:
        n_genre = list_length // 2
        n_prod = list_length - n_genre
    elif has_g:
        n_genre, n_prod = list_length, 0
    else:
        n_genre, n_prod = 0, list_length

    run_seen: set[int] = set()
    skip_tags: set[int] = set()
    skip_prods: set[int] = set()

    genre_items = _collect_weighted_side(
        genre_rows,
        "tag",
        n_genre,
        rng,
        rated_song_ids,
        seen_ids,
        run_seen,
        skip_tags,
        len(genre_rows),
        len(producer_rows),
        session,
    )
    prod_items = _collect_weighted_side(
        producer_rows,
        "producer",
        n_prod,
        rng,
        rated_song_ids,
        seen_ids,
        run_seen,
        skip_prods,
        len(genre_rows),
        len(producer_rows),
        session,
    )

    return _interleave(genre_items, prod_items)


def main(
    user_id: int,
    session: requests.Session,
    author_id: int | None = None,
    list_length: int = LIST_LENGTH,
    state_dir: Path | None = None,
) -> str:
    if author_id is None:
        author_id = user_id

    if state_dir is None:
        state_dir = _default_state_dir()
    state_dir = state_dir.resolve()
    state_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Building advanced recommendation for user {user_id}")

    library = get_user_library(
        user_id,
        collections=frozenset({"rated_songs"}),
        session=session,
    )
    rated_song_ids: set[int] = {int(k) for k in library.rated_songs}
    rated_songs = [
        {"song": e.song, "rating": e.rating, "date": e.date}
        for e in library.rated_songs.values()
    ]

    if not rated_songs:
        raise ValueError(f"No rated songs found for user {user_id}")

    tag_info = build_tag_info_map()
    genre_rows = build_top_favourite_genres(
        rated_songs, tag_info, limit=TOP_FAVOURITES
    )
    producer_rows = build_top_favourite_producers(rated_songs, limit=TOP_FAVOURITES)
    logger.info(f"Top genres (id, name, raw): {[(t[0], t[1]) for t in genre_rows[:5]]}")
    logger.info(
        "Top producers (id, name, raw): "
        f"{[(t[0], t[1]) for t in producer_rows[:5]]}"
    )

    if not genre_rows and not producer_rows:
        raise ValueError("Could not build taste profile, no genres or producers found")

    seen_ids = get_seen_song_ids(user_id, state_dir)
    rng = random.Random()
    rng.seed(user_id * 1_000_003 + datetime.now(tz=UTC).toordinal())

    pairs = _select_songs_split(
        genre_rows,
        producer_rows,
        rated_song_ids,
        seen_ids,
        list_length,
        rng,
        session,
    )

    logger.info(f"Selected {len(pairs)} song(s)")

    if not pairs:
        raise ValueError(
            "No new candidates found (API returned no usable songs, or every hit was "
            "already rated/seen). Try again later or rate more songs."
        )

    song_ids = [song.id for song, _ in pairs]
    notes = [note for _, note in pairs]
    _delete_previous_songlist(session, state_dir, user_id)

    date_str = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    songlist_id = create_or_update_songlist(
        session=session,
        song_ids=song_ids,
        author_id=author_id,
        title=f"Recommendations u/{user_id} ({date_str})",
        notes=notes,
    )

    add_seen_song_ids(user_id, song_ids, state_dir)
    _save_last_songlist_id(state_dir, user_id, songlist_id)

    url = f"{WEBSITE}/SongList/Details/{songlist_id}"
    return f"Created {len(song_ids)}-song recommendation list: {url}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a VocaDB recommendation songlist from a taste profile."
        ),
    )
    parser.add_argument("username", type=str, help="VocaDB username")
    parser.add_argument(
        "--list_length",
        type=int,
        default=LIST_LENGTH,
        help=f"Number of songs in the list (default: {LIST_LENGTH})",
    )
    parser.add_argument(
        "--author_id",
        type=int,
        default=None,
        help="VocaDB user ID to create the list under (defaults to the target user)",
    )
    parser.add_argument(
        "--state_dir",
        type=Path,
        default=None,
        help="Directory for seen IDs and last songlist id",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logger = get_logger("recommend_advanced")
    args = parse_args()

    username, user_id = find_user_by_username_1d(args.username)
    if not user_id:
        logger.error(f"User '{args.username}' not found")
        sys.exit(1)

    un, pw = get_credentials("credentials.env")
    with requests.Session() as session:
        session.post(
            f"{WEBSITE}/api/users/login",
            json={"UserName": un, "password": pw},
        ).raise_for_status()
        result = main(
            user_id=user_id,
            session=session,
            author_id=args.author_id,
            list_length=args.list_length,
            state_dir=args.state_dir,
        )
    logger.info(result)

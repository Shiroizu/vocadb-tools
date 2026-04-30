"""Compare song rating overlap between two VocaDB users."""

import argparse

import requests
from vdbpy.api.songs import get_rated_songs_with_ratings
from vdbpy.api.users import get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger

PROFILE_URL = f"{WEBSITE}/Profile/"

logger = get_logger()


def _fetch(user_id: int, session: requests.Session | None = None) -> dict[int, str]:
    entries = get_rated_songs_with_ratings(user_id, session=session)
    return {e["song"]["id"]: e["rating"] for e in entries}


def main(
    user_id_1: int,
    user_id_2: int,
    session: requests.Session | None = None,
) -> str:
    songs1 = _fetch(user_id_1, session)
    songs2 = _fetch(user_id_2, session)

    ids1 = set(songs1)
    ids2 = set(songs2)
    shared_ids = ids1 & ids2

    total1 = len(ids1)
    total2 = len(ids2)
    shared = len(shared_ids)
    smaller = min(total1, total2)
    overlap_pct = (shared / smaller * 100) if smaller > 0 else 0.0

    both_fav = sum(
        1 for sid in shared_ids
        if songs1[sid] == "Favorite" and songs2[sid] == "Favorite"
    )
    u1_fav_only = sum(
        1 for sid in shared_ids
        if songs1[sid] == "Favorite" and songs2[sid] != "Favorite"
    )
    u2_fav_only = sum(
        1 for sid in shared_ids
        if songs2[sid] == "Favorite" and songs1[sid] != "Favorite"
    )
    agree_fav_pct = (both_fav / shared * 100) if shared > 0 else 0.0

    name1 = get_username_by_id(user_id_1)
    name2 = get_username_by_id(user_id_2)

    lines = [
        f"Rating overlap: {name1} vs {name2}",
        "",
        f"Rated songs: {PROFILE_URL}{name1}: {total1} | {PROFILE_URL}{name2}: {total2}",
        f"Shared: {shared} ({overlap_pct:.1f}%)",
        f"Only in {name1}: {len(ids1 - ids2)}",
        f"Only in {name2}: {len(ids2 - ids1)}",
        "",
        "Among shared songs:",
        f"  Both Favorite: {both_fav} ({agree_fav_pct:.1f}%)",
        f"  Favorite for {name1} only: {u1_fav_only}",
        f"  Favorite for {name2} only: {u2_fav_only}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    logger = get_logger("rating-diff")
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id_1", type=int)
    parser.add_argument("user_id_2", type=int)
    args = parser.parse_args()
    logger.info(main(args.user_id_1, args.user_id_2))

"""Compare followed artist overlap between two VocaDB users."""

import argparse
from collections import Counter

import requests

from vdbpy.api.user_library import get_user_library
from vdbpy.api.users import get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger

PROFILE_URL = f"{WEBSITE}/Profile/"

logger = get_logger()


def _fetch(user_id: int, session: requests.Session | None = None) -> dict[int, str]:
    lib = get_user_library(
        user_id,
        collections=frozenset({"followed_artists"}),
        session=session,
        check_only_if_public=session is None,
    )
    return {ar["id"]: ar.get("artistType", "Unknown") for ar in lib.followed_artists}


def main(
    user_id_1: int,
    user_id_2: int,
    session: requests.Session | None = None,
) -> str:
    artists1 = _fetch(user_id_1, session)
    artists2 = _fetch(user_id_2, session)

    ids1 = set(artists1)
    ids2 = set(artists2)
    shared_ids = ids1 & ids2

    total1 = len(ids1)
    total2 = len(ids2)
    shared = len(shared_ids)
    smaller = min(total1, total2)
    overlap_pct = (shared / smaller * 100) if smaller > 0 else 0.0

    shared_types = Counter(artists1[aid] for aid in shared_ids)

    name1 = get_username_by_id(user_id_1)
    name2 = get_username_by_id(user_id_2)

    lines = [
        "Followed artist overlap:",
        "",
        f"- {PROFILE_URL}{name1} - {total1} followed artists",
        f"- {PROFILE_URL}{name2} - {total2} followed artists",
        "",
        f"Shared: {shared} ({overlap_pct:.1f}%)",
        f"Only for {name1}: {len(ids1 - ids2)}",
        f"Only for {name2}: {len(ids2 - ids1)}",
    ]
    if shared_types:
        lines += ["", f"Shared artists by type ({shared}):"]
        lines += [
            f"  {artist_type}: {count}"
            for artist_type, count in shared_types.most_common()
        ]
    return "\n".join(lines)


def cli() -> None:
    logger = get_logger("followed-artists-diff")
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id_1", type=int)
    parser.add_argument("user_id_2", type=int)
    args = parser.parse_args()
    logger.info(main(args.user_id_1, args.user_id_2))


if __name__ == "__main__":
    cli()

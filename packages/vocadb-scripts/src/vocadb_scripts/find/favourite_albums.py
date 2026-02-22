"""Find favourite albums for user based on rated songs."""

import argparse
from typing import Any

from tabulate import tabulate
from vdbpy.api.albums import get_albums_by_user_id_7d
from vdbpy.api.songs import get_rated_songs_by_user_id_7d
from vdbpy.api.users import (
    get_username_by_id,
)
from vdbpy.config import WEBSITE
from vdbpy.utils.data import truncate_string_with_ellipsis
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

logger = get_logger()


def get_favourite_albums_based_on_songs_by_user_id(user_id: int) -> dict[Any, Any]:
    # TODO test
    fields = [
        "Albums",
        "Artists",
        "PVs",
        "ReleaseEvent",
        "Tags",
        "WebLinks",
        "CultureCodes",
    ]

    rated_songs = get_rated_songs_by_user_id_7d(fields=fields, user_id=user_id)
    rated_albums = get_albums_by_user_id_7d(user_id)

    owned_album_ids: set[int] = set()
    for album in rated_albums:
        owned_album_ids.add(album["album"]["id"])

    album_entries_of_rated_songs: dict[Any, Any] = {}
    for song_entry in rated_songs:
        if "albums" in song_entry["song"]:
            score = 3 if song_entry["rating"] == "Favorite" else 2
            for album in song_entry["song"]["albums"]:
                album_id = album["id"]
                if album_id not in album_entries_of_rated_songs:
                    album_type = album["discType"]
                    if album_type == "Album":
                        album_type = "Original"
                    album_data = {
                        "album_url": f"{WEBSITE}/Al/{album_id}",
                        "album_name": truncate_string_with_ellipsis(album["name"], 39),
                        "album_type": album_type,
                        "score": score,
                        "in_collection": album_id in owned_album_ids,
                    }
                    album_entries_of_rated_songs[album_id] = album_data
                else:
                    album_entries_of_rated_songs[album_id]["score"] += score

    return album_entries_of_rated_songs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "user_id",
        type=int,
        help="VocaDB user id",
    )
    parser.add_argument(
        "--max_results",
        type=int,
        default=25,
        help="Maximum number of results to show",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    user_id = args.user_id
    max_results = args.max_results

    logger = get_logger("find_favourite_albums")
    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite albums for user '{username}' ({user_id})")

    OUTPUT_FILE = f"output/favourite-albums-{user_id}.csv"

    albums = get_favourite_albums_based_on_songs_by_user_id(user_id)
    albums_to_print = list(albums.values())
    albums_to_print.sort(key=lambda x: x["score"], reverse=True)
    table = tabulate(albums_to_print[:max_results], headers="keys", tablefmt="github")
    logger.info(f"\n{table}")

    save_file(OUTPUT_FILE, table)

"""Find favourite albums for user based on rated songs. Example output below.

Searching favourite X for user 'Shiroizu' (329)
Found total of 9122 rated songs.
Found total of 99 albums.

| album_url                   | album_name                                                               | album_type   |   score | in_collection   |
|-----------------------------|--------------------------------------------------------------------------|--------------|---------|-----------------|
| https://vocadb.net/Al/6593  | VOCA NICO☆PARTY                                                          | Compilation  |      37 | False           |
| https://vocadb.net/Al/20091 | Stay Far Away from Me                                                    | Original     |      34 | False           |
| https://vocadb.net/Al/23903 | ELATE                                                                    | Original     |      29 | False           |
| https://vocadb.net/Al/31267 | KAF+YOU KAFU COMPILATION ALBUM シンメトリー (...                         | Compilation  |      28 | False           |
| https://vocadb.net/Al/12206 | Drops                                                                    | Original     |      28 | False           |
| https://vocadb.net/Al/22351 | EXIT TUNES PRESENTS Vocalohistory feat....                               | Compilation  |      28 | False           |
| https://vocadb.net/Al/5182  | V♥25 -Hearts-                                                            | Compilation  |      27 | False           |
| https://vocadb.net/Al/40750 | ボカMIX 39's                                                             | Compilation  |      27 | False           |
| https://vocadb.net/Al/19741 | 3.5 O'Clock!                                                             | Original     |      26 | False           |
| https://vocadb.net/Al/31200 | 初音ミク - ミクの日大感謝祭 LIVE CD                                      | Compilation  |      26 | False           |
| https://vocadb.net/Al/31196 | 初音ミク - ミクの日大感謝祭 2DaysコンプリートBOX                         | Compilation  |      26 | False           |
| https://vocadb.net/Al/3409  | V♥25 -Gloria-                                                            | Compilation  |      25 | False           |
| https://vocadb.net/Al/3369  | EXLIUM                                                                   | SplitAlbum   |      24 | True            |
| https://vocadb.net/Al/18033 | Eight -THE BEST OF 八王子P-                                              | Compilation  |      24 | False           |
| https://vocadb.net/Al/28919 | TOMAYOI                                                                  | Original     |      24 | True            |
| https://vocadb.net/Al/45658 | 初音ミク「マジカルミライ2024」Blu-Ray&DVD                                | Video        |      23 | False           |
| https://vocadb.net/Al/3599  | EXIT TUNES PRESENTS GUMity from Megpoid                                  | Compilation  |      23 | False           |
| https://vocadb.net/Al/29671 | Hatsune Miku Live Party 2013 in Kansai ...                               | Video        |      23 | False           |
| https://vocadb.net/Al/33601 | 初音ミク「マジカルミライ」10th Anniversary Blu-ray&D...                  | Video        |      23 | False           |
| https://vocadb.net/Al/11158 | EVERGREEN SONGS 2013                                                     | Compilation  |      22 | False           |
| https://vocadb.net/Al/149   | on-sawmen                                                                | Original     |      21 | True            |

Table saved to 'output/favourite-albums-329.txt'
"""

import argparse

from tabulate import tabulate
from vdbpy.api.users import (
    get_albums_by_user_id,
    get_rated_songs_by_user_id,
    get_username_by_id,
)
from vdbpy.config import WEBSITE
from vdbpy.utils.data import truncate_string_with_ellipsis
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

logger = get_logger("find-favourite-albums")


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

    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite albums for user '{username}' ({user_id})")

    OUTPUT_FILE = f"output/favourite-albums-{user_id}.csv"

    extra_params = {"fields": "Albums"}
    rated_songs = get_rated_songs_by_user_id(int(user_id), extra_params)
    rated_albums = get_albums_by_user_id(int(user_id))

    owned_album_ids = set()
    for album in rated_albums:
        owned_album_ids.add(album["album"]["id"])

    album_entries_of_rated_songs = {}
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

    albums_to_print = list(album_entries_of_rated_songs.values())

    albums_to_print.sort(key=lambda x: x["score"], reverse=True)
    table = tabulate(albums_to_print[:max_results], headers="keys", tablefmt="github")
    logger.info(f"\n{table}")

    save_file(OUTPUT_FILE, table)

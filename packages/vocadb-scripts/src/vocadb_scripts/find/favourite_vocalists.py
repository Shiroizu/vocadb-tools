"""Find favourite albums for user based on rated songs. Example output below.

  Favs    Likes  Vocalist    Entry
------  -------  ----------  ----------------------------
  1584     3300  初音ミク    https://vocadb.net/Ar/1
   204      587  GUMI        https://vocadb.net/Ar/3
   195      536  鏡音リン    https://vocadb.net/Ar/14
    95      308  IA          https://vocadb.net/Ar/504
   106      283  巡音ルカ    https://vocadb.net/Ar/2
    80      255  鏡音レン    https://vocadb.net/Ar/15
    99      195  結月ゆかり  https://vocadb.net/Ar/134288
    55      215  v flower    https://vocadb.net/Ar/21165
    60      203  可不        https://vocadb.net/Ar/83928
    69      183  重音テト    https://vocadb.net/Ar/140308

Table saved to 'output/favourite-vocalists-329.txt'
"""

import argparse
from datetime import UTC, datetime, timedelta

import tabulate as tabulate_module
from tabulate import tabulate
from vdbpy.api.artists import (
    get_artist_by_id_7d,
    get_cached_base_voicebank_by_artist_id,
)
from vdbpy.api.songs import get_cached_rated_songs_with_ratings
from vdbpy.api.users import get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.utils.cache import get_vdbpy_cache_dir
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

tabulate_module.WIDE_CHARS_MODE = True
logger = get_logger()


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
        default=20,
        help="Maximum number of results to show",
    )
    parser.add_argument(
        "--do_not_group_by_base_vb",
        action="store_true",
        help="Do not group by base voicebank",
    )

    return parser.parse_args()


def main(user_id: int, max_results: int = 20, group_by_base_vb: bool = True) -> str:
    output_path = get_vdbpy_cache_dir() / "favourite-vocalists" / f"{user_id}.txt"
    if output_path.exists():
        age = datetime.now(tz=UTC) - datetime.fromtimestamp(
            output_path.stat().st_mtime, tz=UTC
        )
        if age < timedelta(days=7):
            logger.info(
                f"Cache hit: '{output_path}' is {age.days}d old, skipping rebuild"
            )
            return output_path.read_text(encoding="utf-8")

    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite vocalists for user '{username}' ({user_id})")

    unique_vocalists = {}

    rated_songs = get_cached_rated_songs_with_ratings(user_id)

    for song in rated_songs:
        rating = song["rating"]
        try:
            for artist in song["song"]["artists"]:
                if "Vocalist" in artist["categories"]:
                    artist_id = artist["artist"]["id"]
                    if artist_id in unique_vocalists:
                        if rating == "Favorite":
                            unique_vocalists[artist_id][1] += 1
                        elif rating == "Like":
                            unique_vocalists[artist_id][2] += 1
                    elif rating == "Favorite":
                        unique_vocalists[artist_id] = [artist["artist"]["name"], 1, 0]
                    elif rating == "Like":
                        unique_vocalists[artist_id] = [artist["artist"]["name"], 0, 1]
        except KeyError:
            # logger.info(f"Custom artist '{placeholder}' on S/{song['song']['id']}")
            continue

    unique_vocalists_with_score = []

    for ar_id in unique_vocalists:
        name, favs, likes = [
            unique_vocalists[ar_id][0],
            unique_vocalists[ar_id][1],
            unique_vocalists[ar_id][2],
        ]
        score = favs * 3 + likes * 2
        unique_vocalists_with_score.append([name, favs, likes, score, ar_id])

    if group_by_base_vb:
        score_by_id: dict[int, list[int]] = {}
        for counter, vb in enumerate(unique_vocalists_with_score):
            _, favs, likes, score, vb_id = vb
            base_vb_id = get_cached_base_voicebank_by_artist_id(vb_id)
            if vb_id != base_vb_id:
                logger.info(
                    f"{counter}/{len(unique_vocalists_with_score)} - "
                    f"Base VB for Ar/{vb_id} is Ar/{base_vb_id}"
                )
            if base_vb_id in score_by_id:
                score_by_id[base_vb_id][0] += favs
                score_by_id[base_vb_id][1] += likes
                score_by_id[base_vb_id][2] += score
            else:
                score_by_id[base_vb_id] = [favs, likes, score]
        sorted_ids = sorted(score_by_id, key=lambda i: score_by_id[i][2], reverse=True)
        unique_vocalists_with_score = [
            [get_artist_by_id_7d(ar_id)["name"], *score_by_id[ar_id], ar_id]
            for ar_id in sorted_ids[:max_results]
        ]
    else:
        unique_vocalists_with_score.sort(key=lambda x: x[3], reverse=True)
        unique_vocalists_with_score = unique_vocalists_with_score[:max_results]

    table_to_print = []
    for ar in unique_vocalists_with_score:
        name, favs, likes, score, ar_id = ar
        name = str(name)
        if name.lower().endswith(" (unknown)"):
            name = name[:-10]
        line_to_print = (favs, likes, name, f"{WEBSITE}/Ar/{ar_id}")
        table_to_print.append(line_to_print)

    table = tabulate(
        table_to_print,
        headers=["Favs", "Likes", "Vocalist", "Entry"],
        tablefmt="github",
    )
    save_file(output_path, table)
    logger.info(f"\nTable saved to '{output_path}'")
    return table


if __name__ == "__main__":
    logger = get_logger("find_favourite_vocalists")
    args = parse_args()
    result = main(args.user_id, args.max_results, not args.do_not_group_by_base_vb)
    logger.info(f"\n{result}")

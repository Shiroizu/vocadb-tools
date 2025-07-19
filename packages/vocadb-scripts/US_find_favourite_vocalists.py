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

from tabulate import tabulate
from vdbpy.api.artists import get_artist_by_id, get_base_voicebank_by_artist_id
from vdbpy.api.users import get_rated_songs_by_user_id, get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

logger = get_logger("find-favourite-vocalists")


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


if __name__ == "__main__":
    args = parse_args()
    user_id = args.user_id
    max_results = args.max_results
    group_by_base_vb = not args.do_not_group_by_base_vb

    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite vocalists for user '{username}' ({user_id})")

    OUTPUT_FILE = f"output/favourite-vocalists-{user_id}.txt"

    unique_vocalists = {}
    extra_params = {"fields": "Artists"}
    rated_songs = get_rated_songs_by_user_id(int(user_id), extra_params)

    for song in rated_songs:
        placeholder = ""
        rating = song["rating"]
        try:
            for artist in song["song"]["artists"]:
                if "Vocalist" in artist["categories"]:
                    placeholder = artist["name"]
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
        score_by_base_vb = {}
        # name: [favs, likes, score, id]
        for counter, vb in enumerate(unique_vocalists_with_score):
            vb_name, favs, likes, score, vb_id = vb
            base_vb_id = get_base_voicebank_by_artist_id(vb_id)
            base_vb = get_artist_by_id(base_vb_id)
            base_name = base_vb["name"]
            if vb_name != base_name:
                logger.info(
                    f"{counter+1}/{len(unique_vocalists_with_score)} Base VB for '{vb_name}' is '{base_name}'"
                )
            if base_name in score_by_base_vb:
                score_by_base_vb[base_name][0] += favs
                score_by_base_vb[base_name][1] += likes
                score_by_base_vb[base_name][2] += score
            else:
                score_by_base_vb[base_name] = [favs, likes, score, base_vb["id"]]

        unique_vocalists_with_score = [
            [name, *stats] for name, stats in score_by_base_vb.items()
        ]

    unique_vocalists_with_score.sort(key=lambda x: x[3], reverse=True)

    table_to_print = []
    for ar in unique_vocalists_with_score[:max_results]:
        name, favs, likes, score, ar_id = ar
        if name.lower().endswith(" (unknown)"):
            name = name[:-10]
        line_to_print = (favs, likes, name, f"{WEBSITE}/Ar/{ar_id}")
        table_to_print.append(line_to_print)

    table = tabulate(
        table_to_print,
        headers=["Favs", "Likes", "Vocalist", "Entry"],
        tablefmt="github",
    )
    logger.info(f"\n{table}")

    save_file(OUTPUT_FILE, table)
    logger.info(f"\nTable saved to '{OUTPUT_FILE}'")

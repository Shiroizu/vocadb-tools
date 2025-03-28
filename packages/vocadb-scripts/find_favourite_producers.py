"""Print user's favourite producers based on rated songs.

find-favourite-producers.py 329

  Favs    Likes  Artist            Entry
------  -------  ----------------  -------------------------------------------
    59       43  Kuroneko Lounge   https://vocadb.net/Ar/1063
    73        6  Clean Tears       https://vocadb.net/Ar/20
    58       17  TKN               https://vocadb.net/Ar/19059
    44       25  オカメP           https://vocadb.net/Ar/87
    50        2  鼻そうめんP       https://vocadb.net/Ar/175
    28       23  Osanzi            https://vocadb.net/Ar/18777
    26       23  LIQ               https://vocadb.net/Ar/88
    29        8  Alpaca            https://vocadb.net/Ar/44866
    22       16  鬱P               https://vocadb.net/Ar/90 (not following)
    22       16  Twinfield         https://vocadb.net/Ar/4828
    27        6  ddh               https://vocadb.net/Ar/4724
    20       16  八王子P           https://vocadb.net/Ar/38
    14       25  雄之助            https://vocadb.net/Ar/23981
    16       21  PLAMA             https://vocadb.net/Ar/46360
    19       12  Transient Energy  https://vocadb.net/Ar/16023
    12       21  攻                https://vocadb.net/Ar/13271 (not following)
    16       13  AVTechNO!         https://vocadb.net/Ar/40
    19        7  Spacelectro       https://vocadb.net/Ar/11722
    17       10  Mwk               https://vocadb.net/Ar/16866
    14       14  Giga              https://vocadb.net/Ar/772

Table saved to 'output/favourite-producers-329.txt'
"""

import argparse

from tabulate import tabulate

from api.users import get_followed_artists, get_rated_songs
from utils.files import save_file
from utils.logger import get_logger

logger = get_logger("find-favourite-producers")


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

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    user_id = args.user_id
    max_results = args.max_results

    OUTPUT_FILE = f"output/favourite-producers-{user_id}.csv"

    unique_artists = {}
    extra_params = {"fields": "Artists"}
    rated_songs = get_rated_songs(int(user_id), extra_params)

    for song in rated_songs:
        placeholder = ""
        rating = song["rating"]
        try:
            for artist in song["song"]["artists"]:
                if "Producer" in artist["categories"]:
                    placeholder = artist["name"]
                    artist_id = artist["artist"]["id"]
                    if artist_id in unique_artists:
                        if rating == "Favorite":
                            unique_artists[artist_id][1] += 1
                        elif rating == "Like":
                            unique_artists[artist_id][2] += 1
                    elif rating == "Favorite":
                        unique_artists[artist_id] = [artist["artist"]["name"], 1, 0]
                    elif rating == "Like":
                        unique_artists[artist_id] = [artist["artist"]["name"], 0, 1]

        except KeyError:
            logger.debug(f"Custom artist '{placeholder}' on S/{song['song']['id']}")
            continue

    unique_artists_with_score = []

    for ar_id in unique_artists:
        name, favs, likes = [
            unique_artists[ar_id][0],
            unique_artists[ar_id][1],
            unique_artists[ar_id][2],
        ]
        score = favs * 3 + likes * 2
        unique_artists_with_score.append([name, favs, likes, score, ar_id])

    unique_artists_with_score.sort(key=lambda x: x[3], reverse=True)

    followed_artists = []
    page = 1

    followed_artists = get_followed_artists(user_id)
    followed_artists_ids = [int(artist["id"]) for artist in followed_artists]

    if not max_results:
        max_results = None

    table_to_print = []
    for ar in unique_artists_with_score[:max_results]:
        follow_msg = "(not following)"
        name, favs, likes, score, ar_id = ar
        if int(ar_id) in followed_artists_ids:
            follow_msg = ""
        line_to_print = (
            favs,
            likes,
            name,
            f"https://vocadb.net/Ar/{ar_id} {follow_msg}",
        )
        table_to_print.append(line_to_print)

    table = tabulate(table_to_print, headers=["Favs", "Likes", "Artist", "Entry"])
    logger.info(f"\n{table}")

    save_file(OUTPUT_FILE, table)
    logger.info(f"\nTable saved to '{OUTPUT_FILE}'")

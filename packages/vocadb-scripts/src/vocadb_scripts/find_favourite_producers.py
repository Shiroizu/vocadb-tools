"""Find favourite albums for user based on rated songs. Example output below.

|   Score |   Favs |   Likes |   Favs/Likes |   Rated % | Artist           | Entry                                       |
|---------|--------|---------|--------------|-----------|------------------|---------------------------------------------|
|     263 |     59 |      43 |          1.4 |      32.5 | Kuroneko Lounge  | https://vocadb.net/Ar/1063                  |
|     231 |     73 |       6 |         12.2 |      23.7 | Clean Tears      | https://vocadb.net/Ar/20                    |
|     208 |     58 |      17 |          3.4 |      44.4 | TKN              | https://vocadb.net/Ar/19059                 |
|     182 |     44 |      25 |          1.8 |        23 | オカメP          | https://vocadb.net/Ar/87                    |
|     154 |     50 |       2 |           25 |      73.2 | 鼻そうめんP      | https://vocadb.net/Ar/175                   |
|     130 |     28 |      23 |          1.2 |      36.7 | Osanzi           | https://vocadb.net/Ar/18777                 |
|     124 |     26 |      23 |          1.1 |      40.5 | LIQ              | https://vocadb.net/Ar/88                    |
|     103 |     29 |       8 |          3.6 |      38.5 | Alpaca           | https://vocadb.net/Ar/44866                 |
|     100 |     22 |      17 |          1.3 |      13.7 | 鬱P              | https://vocadb.net/Ar/90 (not following)    |
|      98 |     22 |      16 |          1.4 |      30.2 | Twinfield        | https://vocadb.net/Ar/4828                  |
|      93 |     27 |       6 |          4.5 |      56.9 | ddh              | https://vocadb.net/Ar/4724                  |
|      92 |     20 |      16 |          1.2 |      16.4 | 八王子P          | https://vocadb.net/Ar/38                    |
|      92 |     14 |      25 |          0.6 |      24.1 | 雄之助           | https://vocadb.net/Ar/23981                 |
|      90 |     16 |      21 |          0.8 |      28.2 | PLAMA            | https://vocadb.net/Ar/46360                 |
|      81 |     19 |      12 |          1.6 |         9 | Transient Energy | https://vocadb.net/Ar/16023                 |
|      78 |     12 |      21 |          0.6 |      42.3 | 攻               | https://vocadb.net/Ar/13271 (not following) |
|      74 |     16 |      13 |          1.2 |       8.3 | AVTechNO!        | https://vocadb.net/Ar/40                    |
|      71 |     19 |       7 |          2.7 |      14.6 | Spacelectro      | https://vocadb.net/Ar/11722                 |
|      71 |     17 |      10 |          1.7 |      20.8 | Mwk              | https://vocadb.net/Ar/16866                 |
|      70 |     14 |      14 |            1 |        23 | Giga             | https://vocadb.net/Ar/772                   |

Table saved to 'output/favourite-producers-329.txt'
"""

# TODO add --exclude_new_songs

import argparse

from tabulate import tabulate

from vdbpy.api.artists import get_song_count
from vdbpy.api.users import get_followed_artists, get_rated_songs, get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

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

    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite producers for user '{username}' ({user_id})")

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
        songcount_by_artist = get_song_count(int(ar_id), only_main_songs=True)
        rated_songs_percentage = round(((favs + likes) / songcount_by_artist * 100), 1)
        if int(ar_id) in followed_artists_ids:
            follow_msg = ""
        headers = ["Score", "Favs", "Likes", "Favs/Likes", "Rated %", "Artist", "Entry"]
        line_to_print = (
            score,
            favs,
            likes,
            round(favs / likes, 1) if likes else "",
            rated_songs_percentage,
            name,
            f"{WEBSITE}//Ar/{ar_id} {follow_msg}",
        )
        table_to_print.append(line_to_print)

    table = tabulate(
        table_to_print, headers=headers, tablefmt="github", numalign="right"
    )
    logger.info(f"\n{table}")

    save_file(OUTPUT_FILE, table)
    logger.info(f"\nTable saved to '{OUTPUT_FILE}'")

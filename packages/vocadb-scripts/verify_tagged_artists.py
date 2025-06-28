import argparse

from tabulate import tabulate
from vdbpy.api.artists import get_artists_by_tag_id, get_song_count_by_artist_id
from vdbpy.api.tags import get_tag_by_id
from vdbpy.utils.logger import get_logger

""" Example output:
Tagged artists for 'new wave' (Genres) (T/3251)
| artist           |     id |   tagged |   total | percentage   |
|------------------|--------|----------|---------|--------------|
| 園山モル          |    542 |       15 |      37 | 40 %         |
| Astrophysics     |  99484 |        6 |      30 | 20 %         |
| ぶっちぎりP       |    128 |        5 |      37 | 13 %         |
| 砂粒             |   4980 |        5 |      41 | 12 %         |
| ds_8             |    981 |        4 |      50 | 8 %          |
| kihirohito       |    824 |        4 |     115 | 3 %          |
| liesco           |  69603 |        4 |      62 | 6 %          |
| キャプテンミライ  |    741 |        4 |      89 | 4 %          |
| こえだ、         |  76739 |        4 |      76 | 5 %          |
| 耳ロボP          |    677 |        4 |      97 | 4 %          |
| P-Model          | 151302 |        3 |      35 | 8 %          |
| オサダユーマ      |   5300 |        3 |      37 | 8 %          |
| 宇田もずく        |  54547 |        3 |      56 | 5 %          |
| NaR              |  89300 |        2 |      67 | 2 %          |
| omi              |  85569 |        2 |      34 | 5 %          |
| ondo             |  83943 |        2 |      90 | 2 %          |
| r-906            |  66139 |        2 |      70 | 2 %          |
| slowwaves        | 112068 |        2 |       7 | 28 %         |
| wowaka           |     53 |        2 |      51 | 3 %          |
| いちごのせP      |  68659 |        2 |      40 | 5 %          |
| 是               |  64659 |        2 |      47 | 4 %          |
| 江戸川リバ子     |  26917 |        2 |     125 | 1 %          |
| 田中和夫         |   1919 |        2 |      48 | 4 %          |
| 難解世界P        |  34014 |        2 |      11 | 18 %         |
| TOBEFOOPERS      |  59065 |        1 |     290 | 0 %          |
| 呆               |  58051 |        1 |     102 | 0 %          |
| Saeki Kenzou     |  60403 |        0 |       0 | ∞            |
| パルサ           |  70728 |        0 |      13 | 0 %          |
| 九嬢ねぎ         |   6125 |        0 |      54 | 0 %          |
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tag_id",
        type=int,
        help="Tag id to check.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    logger = get_logger("verify_tagged_artists")
    args = parse_args()

    tag_id = args.tag_id
    tag_entry = get_tag_by_id(tag_id)

    artists_by_tag = get_artists_by_tag_id(tag_id)
    logger.info(
        f"\nFound {len(artists_by_tag)} artists tagged with '{tag_entry['name']}' (T/{tag_id})"
    )
    tagged_entry_counts = {}

    counter = 1

    for artist in artists_by_tag:
        logger.info(f"Artist {counter}/{len(artists_by_tag)}")
        counter += 1
        params = {"tagId[]": tag_id}
        tagged_song_count = get_song_count_by_artist_id(
            artist["id"], only_main_songs=True, extra_params=params
        )
        songs_total = get_song_count_by_artist_id(artist["id"], only_main_songs=True)
        line = {
            "artist": artist["name"],
            "id": artist["id"],
            "tagged": tagged_song_count,
            "total": songs_total,
        }
        logger.debug(line)
        tagged_entry_counts[artist["id"]] = line

    artists_to_print = tagged_entry_counts.values()
    sorted_by_entry_count = sorted(
        artists_to_print, key=lambda x: x["tagged"], reverse=True
    )
    for artist in sorted_by_entry_count:
        percentage = (
            str(100 * artist["tagged"] // artist["total"]) + " %"
            if artist["total"]
            else "∞"
        )
        artist["percentage"] = percentage

    logger.info(
        f"\nTag '{tag_entry['name']}' ({tag_entry['categoryName']}) (T/{tag_id}) - Most relevant artists:"
    )
    logger.info(tabulate(sorted_by_entry_count, headers="keys", tablefmt="github"))

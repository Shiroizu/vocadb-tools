import argparse

from tabulate import tabulate

from api.artists import get_artist, get_song_count
from api.songs import get_songs_by_tag
from api.tags import get_tag
from utils.logger import get_logger

""" Example output:
 Tag 'dark wave' (Genres) (T/3383) - Most relevant artists:
|   entry_count |   songs_total | name             | artist_type   |   artist_id | tagged   | percentage   |
|---------------|---------------|------------------|---------------|-------------|----------|--------------|
|            14 |           106 | 사자춤           | Producer      |       31101 | True     | 13 %         |
|             7 |           199 | Petridisch       | Producer      |       49916 | True     | 3 %          |
|             5 |           285 | Art Dave         | Producer      |       41275 | False    | 1 %          |
|             5 |            30 | Astrophysics     | Producer      |       99484 | True     | 16 %         |
|             3 |           371 | Leshy-P          | Producer      |       78451 | False    | 0 %          |
|             3 |            62 | liesco           | Producer      |       69603 | False    | 4 %          |
|             2 |             5 | *=66             | Producer      |       68136 | True     | 40 %         |
|             2 |           108 | S.O.U.L.         | Producer      |       35841 | False    | 1 %          |
|             1 |            38 | PizzaLynne       | Producer      |       77327 | False    | 2 %          |
|             1 |            91 | Yamaji           | Producer      |        1278 | True     | 1 %          |
|             1 |            71 | Lil Daisy        | Producer      |      118064 | False    | 1 %          |
|             1 |            28 | HYPNOPOSSUM      | Producer      |      129478 | False    | 3 %          |
|             1 |            21 | General Nuisance | CoverArtist   |       98712 | False    | 4 %          |
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tag_id",
        type=int,
        help="Tag id to check.",
    )
    parser.add_argument(
        "--producers_only",
        help="Only include producers artists from the entries.",
        action="store_true",
    )
    parser.add_argument(
        "--include_supporting_artists",
        help="Skip artists who are in a supporting role.",
        action="store_true",
    )

    return parser.parse_args()


if __name__ == "__main__":
    logger = get_logger("calculate_most_relevant_artists_by_a_tag")
    args = parse_args()
    producers_only = args.producers_only
    skip_supporting_artists = not args.include_supporting_artists

    tag_id = args.tag_id
    tag_entry = get_tag(tag_id)

    params = {"fields": "artists"}
    songs_by_tag = get_songs_by_tag(tag_id, params)
    logger.info(f"\nFound {len(songs_by_tag)} songs")
    song_counts = {}

    counter = 1

    for song in songs_by_tag:
        logger.info(f"Song {counter}/{len(songs_by_tag)}:")
        counter += 1
        for artist in song["artists"]:
            if "artist" not in artist:
                continue  # custom artist

            if producers_only and artist["categories"] != "Producer":
                continue

            if skip_supporting_artists and artist["isSupport"]:
                continue

            """
            "additionalNames": "Minatsuki Toka, PandoristP, ...
            "artistType": "Producer",
            "deleted": false,
            "id": 278,
            "name": "ミナツキトーカ",
            "pictureMime": "image/jpeg",
            "status": "Finished",
            "version": 25
            """

            artist_data = artist["artist"]
            artist_id = artist_data["id"]

            if artist_id not in song_counts:
                if skip_supporting_artists:
                    songcount_by_artist = get_song_count(
                        artist_id, only_main_songs=True
                    )
                else:
                    songcount_by_artist = get_song_count(
                        artist_id, only_main_songs=False
                    )

                artist_entry = get_artist(artist_id, fields="Tags")
                artist_entry_tag_ids = [
                    tag["tag"]["id"] for tag in artist_entry["tags"]
                ]

                song_counts[artist_id] = {
                    "entry_count": 1,
                    "songs_total": songcount_by_artist,
                    "name": artist_data["name"],
                    "artist_type": artist_data["artistType"],
                    "artist_id": artist_id,
                    "tagged": tag_id in artist_entry_tag_ids,
                }
            else:
                song_counts[artist_id]["entry_count"] += 1

            logger.info(f"\t{song_counts[artist_id]}")

    artists_to_print = song_counts.values()
    sorted_by_entry_count = sorted(
        artists_to_print, key=lambda x: x["entry_count"], reverse=True
    )
    for artist in sorted_by_entry_count:
        percentage = str(100 * artist["entry_count"] // artist["songs_total"]) + " %"
        artist["percentage"] = percentage

    logger.info(
        f"\nTag '{tag_entry['name']}' ({tag_entry['categoryName']}) (T/{tag_id}) - Most relevant artists:"
    )
    logger.info(tabulate(sorted_by_entry_count, headers="keys", tablefmt="github"))

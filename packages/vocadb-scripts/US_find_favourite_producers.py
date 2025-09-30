"""Generate a table of user's favourite producers."""

# TODO youtube channel
# TODO include most popular song
# TODO include latest song publish date

import argparse

from tabulate import tabulate
from vdbpy.api.artists import get_song_count_by_artist_id
from vdbpy.api.users import (
    get_albums_by_user_id,
    get_followed_artists_by_user_id,
    get_rated_songs_by_user_id,
    get_username_by_id,
)
from vdbpy.config import WEBSITE
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

logger = get_logger("find-favourite-producers")


def find_favourite_producers_by_user_id(user_id: int, max_results):
    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite producers for user '{username}' ({user_id})")

    unique_artists = {}

    fields = [
        "Albums",
        "Artists",
        "PVs",
        "ReleaseEvent",
        "Tags",
        "WebLinks",
        "CultureCodes",
    ]

    params = {"fields": ", ".join(fields)}
    rated_songs = get_rated_songs_by_user_id(user_id, params)
    # TODO permanent* cache

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
                        unique_artists[artist_id] = [
                            artist["artist"]["name"],
                            1,
                            0,
                            0,
                            0,
                        ]
                    elif rating == "Like":
                        unique_artists[artist_id] = [
                            artist["artist"]["name"],
                            0,
                            1,
                            0,
                            0,
                        ]

        except KeyError:
            logger.debug(f"Custom artist '{placeholder}' on S/{song['song']['id']}")
            continue

    albums = get_albums_by_user_id(user_id, extra_params={"fields": "Artists, Tracks"})
    for album in albums:
        album_producers_ids_by_name = {
            artist["artist"]["name"]: artist["artist"]["id"]
            for artist in album["album"]["artists"]
            if artist["categories"] == "Producer" and "artist" in artist
        }
        for artist in album["album"]["artists"]:
            if artist["categories"] != "Producer" or artist["isSupport"]:
                continue
            if artist["artist"]["id"] in unique_artists:
                unique_artists[artist["artist"]["id"]][3] += 1
            else:
                unique_artists[artist["artist"]["id"]] = [
                    artist["artist"]["name"],
                    0,
                    0,
                    1,
                    0,
                ]
        for track in album["album"]["tracks"]:
            artist_name_from_artist_string = track["song"]["artistString"].split(
                " feat. "
            )[0]
            artist_id = album_producers_ids_by_name.get(
                artist_name_from_artist_string, 0
            )
            if artist_id in unique_artists:
                unique_artists[artist_id][4] += 1
            else:
                logger.info(
                    f"Album '{album['album']['name']}': Found an unknown tracklist artist '{artist_name_from_artist_string}'"
                )
                logger.info(f"Album producers: {album_producers_ids_by_name}")
    logger.info(f"Analyzed {len(albums)} albums...")
    logger.info(f"Found {len(unique_artists)} unique artists...")

    unique_artists_with_score = []
    for ar_id in unique_artists:
        name, favs, likes, album_count, album_track_count = [
            unique_artists[ar_id][0],
            unique_artists[ar_id][1],
            unique_artists[ar_id][2],
            unique_artists[ar_id][3],
            unique_artists[ar_id][4],
        ]
        score = favs * 3 + likes * 2 + 10 * album_count + album_track_count
        unique_artists_with_score.append(
            [name, favs, likes, score, ar_id, album_count, album_track_count]
        )

    unique_artists_with_score.sort(key=lambda x: x[3], reverse=True)

    followed_artists = []
    logger.info("Fetching followed artists...")
    followed_artists = get_followed_artists_by_user_id(user_id)
    followed_artists_ids = [int(artist["id"]) for artist in followed_artists]

    table_to_print = []
    for ar in unique_artists_with_score[:max_results]:
        logger.info(f"Generating row for artist {ar}...")
        following = False
        name, favs, likes, score, ar_id, album_count, album_track_count = ar
        songcount_by_artist = get_song_count_by_artist_id(
            int(ar_id), only_main_songs=True
        )
        rated_songs_percentage = round(((favs + likes) / songcount_by_artist * 100), 1)
        if int(ar_id) in followed_artists_ids:
            following = True
        headers = [
            "Score",
            "Favs",
            "Likes",
            "Favs/Likes",
            "Rated %",
            "Album count",
            "Album track count",
            "Artist",
            "Following",
            "Entry",
        ]
        line_to_print = (
            score,
            favs,
            likes,
            round(favs / likes, 1) if likes else "",
            rated_songs_percentage,
            album_count,
            album_track_count,
            name,
            following,
            f"{WEBSITE}/Ar/{ar_id}",
        )
        table_to_print.append(line_to_print)

    return headers, table_to_print


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
    headers, producer_table = find_favourite_producers_by_user_id(user_id, max_results)
    logger.info(f"Got {len(producer_table)} producers...")
    table = tabulate(
        producer_table, headers=headers, tablefmt="github", numalign="right"
    )
    logger.info(f"\n{table}")
    save_file(OUTPUT_FILE, table)
    logger.info(f"\nTable saved to '{OUTPUT_FILE}'")

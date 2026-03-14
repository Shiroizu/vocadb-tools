"""Generate a table of user's favourite producers."""

# TODO ignore non-music-producers

import argparse
from datetime import UTC, datetime, timedelta
from typing import Any

from tabulate import tabulate
from vdbpy.api.albums import get_cached_albums_by_user_id
from vdbpy.api.artists import (
    get_artist_by_id_7d,
    get_cached_followed_artists_by_user_id,
    get_song_count_by_artist_id_30d,
)
from vdbpy.api.songs import (
    get_cached_rated_songs_with_ratings,
    get_most_rated_song_by_artist_id_7d,
    get_most_recent_song_by_artist_id_1d,
)
from vdbpy.api.users import get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.utils.cache import get_vdbpy_cache_dir
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

logger = get_logger()


def get_youtube_link(artist_entry: dict[Any, Any]) -> str:
    if "webLinks" not in artist_entry:
        logger.warning("Artist entry does not include any external links!")
        return ""
    for link in artist_entry["webLinks"]:
        if (
            link["category"] == "Official"
            and not link["disabled"]
            and link["url"].startswith("https://www.youtube.com/")
        ):
            return link["url"]
    return ""


def get_days_since_song_publish_date(song_entry, today: datetime) -> int:
    if not song_entry.publish_date:
        logger.warning(f"Song {song_entry.id} does not include a publish date!")
        return -1

    if song_entry.publish_date > today:
        logger.warning(f"Song {song_entry.id} has a publish date in the future!")
        return -1

    return (today - song_entry.publish_date).days


def find_favourite_producers_by_user_id(user_id: int, max_results: int):
    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite producers for user '{username}' ({user_id})")

    unique_artists = {}

    rated_songs = get_cached_rated_songs_with_ratings(user_id)

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

    albums = get_cached_albums_by_user_id(user_id)
    for album in albums:
        album_producers_ids_by_name = {
            artist["artist"]["name"]: artist["artist"]["id"]
            for artist in album["album"]["artists"]
            if artist["categories"] == "Producer" and "artist" in artist
        }
        for artist in album["album"]["artists"]:
            if "artist" not in artist:
                continue
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
        if "tracks" not in album["album"]:
            logger.warning(f"Album '{album['album']['name']}' has no tracks!")
            continue
        for track in album["album"]["tracks"]:
            if "song" not in track:
                continue
            producer_string = track["song"]["artistString"].split(" feat. ")[0]
            producer_names = [n.strip() for n in producer_string.split(", ")]
            for producer_name in producer_names:
                artist_id = album_producers_ids_by_name.get(producer_name, 0)
                if artist_id in unique_artists:
                    unique_artists[artist_id][4] += 1
                elif artist_id:
                    unique_artists[artist_id] = [producer_name, 0, 0, 0, 1]
                else:
                    logger.info(
                        f"Album '{album['album']['name']}': Found an unknown tracklist"
                        f" artist '{producer_name}'"
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

    logger.info("Fetching followed artists...")
    followed_artists = get_cached_followed_artists_by_user_id(user_id)
    followed_artists_ids = [int(artist["id"]) for artist in followed_artists]

    headers = [
        "Score",
        "Artist",
        "Favs",
        "Likes",
        "Favs/Likes",
        "Rated %",
        "Album count",
        "Track count",
        "Following",
        "Entry",
        "Youtube",
        "Most rated song",
        "Days since last song",
    ]
    table_to_print = []
    today = datetime.now(tz=UTC)
    for counter, ar in enumerate(unique_artists_with_score[:max_results], start=1):
        logger.info(f"Generating row for artist {counter}/{max_results}: {ar}...")
        name, favs, likes, score, ar_id, album_count, album_track_count = ar
        artist_entry = get_artist_by_id_7d(ar_id, fields=["webLinks"])
        songcount_by_artist = get_song_count_by_artist_id_30d(
            ar_id, only_main_songs=True
        )
        rated_songs_percentage = (
            round(((favs + likes) / songcount_by_artist * 100), 1)
            if songcount_by_artist
            else 0
        )
        most_rated_song = get_most_rated_song_by_artist_id_7d(ar_id)
        most_recent_song = get_most_recent_song_by_artist_id_1d(ar_id)
        line_to_print = (
            score,
            name,
            favs,
            likes,
            round(favs / likes, 1) if likes else 0,
            rated_songs_percentage,
            album_count,
            album_track_count,
            ar_id in followed_artists_ids,
            f"{WEBSITE}/Ar/{ar_id}",
            get_youtube_link(artist_entry),
            f"{WEBSITE}/S/{most_rated_song.id}",
            get_days_since_song_publish_date(most_recent_song, today),
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


def main(user_id: int, max_results: int = 20) -> str:
    output_path = get_vdbpy_cache_dir() / "favourite-producers" / f"{user_id}.csv"
    if output_path.exists():
        age = datetime.now(tz=UTC) - datetime.fromtimestamp(
            output_path.stat().st_mtime, tz=UTC
        )
        if age < timedelta(days=7):
            logger.info(
                f"Cache hit: '{output_path}' is {age.days}d old, skipping rebuild"
            )
            return output_path.read_text(encoding="utf-8")
    headers, producer_table = find_favourite_producers_by_user_id(user_id, max_results)
    table = tabulate(
        producer_table, headers=headers, tablefmt="github", numalign="right"
    )
    save_file(output_path, table)
    logger.info(f"\nTable saved to '{output_path}'")
    return table


if __name__ == "__main__":
    args = parse_args()
    logger = get_logger("find_favourite_producers")
    result = main(args.user_id, args.max_results)
    logger.info(f"\n{result}")

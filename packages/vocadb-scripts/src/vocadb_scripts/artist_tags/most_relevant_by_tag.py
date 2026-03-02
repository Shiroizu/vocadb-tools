import argparse
from typing import Any

from tabulate import tabulate
from vdbpy.api.artists import get_artist_by_id_1d, get_song_count_by_artist_id_1d
from vdbpy.api.songs import SongSearchParams, get_songs_with_total_count
from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger

logger = get_logger()

MAX_SONGS = 50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tag_id",
        type=int,
        help="Tag id to check.",
    )
    parser.add_argument(
        "--all_artists",
        help="Include all artist types, not just producers.",
        action="store_true",
    )
    parser.add_argument(
        "--include_supporting_artists",
        help="Skip artists who are in a supporting role.",
        action="store_true",
    )

    return parser.parse_args()


def get_relevant_tag_artists_table(
    tag_id: int, skip_supporting_artists: bool = False, producers_only: bool = False
) -> tuple[list[dict[str, Any]], bool]:
    # TODO test
    songs_by_tag, total_count = get_songs_with_total_count(
        fields={"artists"},
        song_search_params=SongSearchParams(tag_ids={tag_id}, max_results=MAX_SONGS),
    )
    truncated = total_count > MAX_SONGS
    if truncated:
        logger.warning("Only the first 50 songs will be checked!")
    logger.info(f"\nFound {len(songs_by_tag)} songs")
    song_counts: dict[int, dict[str, Any]] = {}

    for counter, song in enumerate(songs_by_tag):
        logger.info(f"Song {counter}/{len(songs_by_tag[:MAX_SONGS])}:")
        assert song.artists != "Unknown"  # noqa: S101
        for artist in song.artists:
            if artist.entry == "Custom artist":
                continue

            artist_id = artist.entry.artist_id
            if producers_only and "Producer" not in artist.categories:
                continue

            if skip_supporting_artists and artist.is_support:
                continue

            if artist_id not in song_counts:
                songcount_by_artist = get_song_count_by_artist_id_1d(
                    artist_id, only_main_songs=skip_supporting_artists
                )

                artist_entry = get_artist_by_id_1d(artist_id, fields=["Tags"])
                artist_entry_tag_ids = [
                    tag["tag"]["id"] for tag in artist_entry["tags"]
                ]

                song_counts[artist_id] = {
                    "entry_count": 1,
                    "songs_total": songcount_by_artist,
                    "name": artist_entry["name"],
                    "artist_type": artist_entry["artistType"],
                    "artist_id": artist_id,
                    "tagged": tag_id in artist_entry_tag_ids,
                }
            else:
                song_counts[artist_id]["entry_count"] += 1

            logger.debug(f"\t{song_counts[artist_id]}")

    artists_to_print = song_counts.values()
    sorted_by_entry_count = sorted(
        artists_to_print, key=lambda x: x["entry_count"], reverse=True
    )
    for artist in sorted_by_entry_count:
        percentage = str(100 * artist["entry_count"] // artist["songs_total"]) + " %"
        artist["percentage"] = percentage

    return sorted_by_entry_count, truncated


if __name__ == "__main__":
    logger = get_logger("most_relevant_artist_tags")
    args = parse_args()
    producers_only = not args.all_artists
    skip_supporting_artists = not args.include_supporting_artists

    tag_id = args.tag_id
    table, truncated = get_relevant_tag_artists_table(
        tag_id,
        skip_supporting_artists=skip_supporting_artists,
        producers_only=producers_only,
    )

    logger.info(f"\nTag ({WEBSITE}/T/{tag_id}) - Most relevant artists:")
    if truncated:
        logger.warning(f"Results limited to first {MAX_SONGS} songs.")
    logger.info(tabulate(table, headers="keys", tablefmt="github"))

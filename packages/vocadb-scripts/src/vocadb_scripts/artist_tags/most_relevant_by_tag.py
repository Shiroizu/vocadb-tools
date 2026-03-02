import argparse
from typing import Any

from tabulate import tabulate
from vdbpy.api.artists import get_artist_by_id
from vdbpy.api.songs import SongSearchParams, get_songs, get_songs_with_total_count
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


def get_relevant_tag_artists_table(
    tag_id: int, skip_supporting_artists: bool = False, producers_only: bool = False
) -> list[dict[str, Any]]:
    # TODO test
    songs_by_tag = get_songs(
        fields={"artists"}, song_search_params=SongSearchParams(tag_ids={tag_id})
    )
    if len(songs_by_tag) > MAX_SONGS:
        logger.warning("Only the first 50 songs will be checked!")
    logger.info(f"\nFound {len(songs_by_tag)} songs")
    song_counts: dict[int, dict[str, Any]] = {}

    for counter, song in enumerate(songs_by_tag[:MAX_SONGS]):
        logger.info(f"Song {counter}/{len(songs_by_tag[:MAX_SONGS])}:")
        assert song.artists != "Unknown"  # noqa: S101
        for artist in song.artists:
            if artist.entry == "Custom artist":
                continue

            artist_id = artist.entry.artist_id
            if producers_only and artist.categories != "Producer":
                continue

            if skip_supporting_artists and artist.is_support:
                continue

            if artist_id not in song_counts:
                # TODO convert to fetch_total_count_30d
                if skip_supporting_artists:
                    _, songcount_by_artist = get_songs_with_total_count(
                        song_search_params=SongSearchParams(
                            artist_participation_status="OnlyMainAlbums",
                            artist_ids={artist_id},
                            max_results=1,
                        )
                    )
                else:
                    songcount_by_artist = get_songs_with_total_count(
                        song_search_params=SongSearchParams(
                            artist_participation_status="Everything",
                            artist_ids={artist_id},
                            max_results=1,
                        )
                    )

                artist_entry = get_artist_by_id(artist_id, fields=["Tags"])
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

            logger.info(f"\t{song_counts[artist_id]}")

    artists_to_print = song_counts.values()
    sorted_by_entry_count = sorted(
        artists_to_print, key=lambda x: x["entry_count"], reverse=True
    )
    for artist in sorted_by_entry_count:
        percentage = str(100 * artist["entry_count"] // artist["songs_total"]) + " %"
        artist["percentage"] = percentage

    return sorted_by_entry_count


if __name__ == "__main__":
    logger = get_logger("most_relevant_artist_tags")
    args = parse_args()
    producers_only = args.producers_only
    skip_supporting_artists = not args.include_supporting_artists

    tag_id = args.tag_id
    table = get_relevant_tag_artists_table(
        tag_id,
        skip_supporting_artists=skip_supporting_artists,
        producers_only=producers_only,
    )

    logger.info(f"\nTag ({WEBSITE}/T/{tag_id}) - Most relevant artists:")
    logger.info(tabulate(table, headers="keys", tablefmt="github"))

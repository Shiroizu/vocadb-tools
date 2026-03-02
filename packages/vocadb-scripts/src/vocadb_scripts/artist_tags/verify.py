import argparse
from typing import Any

from tabulate import tabulate
from vdbpy.api.artists import get_artists_by_tag_id
from vdbpy.api.songs import SongSearchParams, get_songs_with_total_count
from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger

MAX_ARTISTS = 50

logger = get_logger()


def get_tagged_artists_table(tag_id: int) -> list[Any]:
    # TODO test
    artists_by_tag = get_artists_by_tag_id(tag_id)
    logger.info(
        f"\nFound {len(artists_by_tag)} artists tagged with {WEBSITE}/T/{tag_id})"
    )
    if len(artists_by_tag) > MAX_ARTISTS:
        logger.warning("Only the first 50 artists will be included in the table")
    tagged_entry_counts: dict[str, Any] = {}

    for counter, artist in enumerate(artists_by_tag[:MAX_ARTISTS]):
        logger.info(f"Artist {counter}/{len(artists_by_tag)}")
        _, tagged_song_count = get_songs_with_total_count(
            song_search_params=SongSearchParams(
                artist_ids=artist["id"],
                artist_participation_status="OnlyMainAlbums",
                tag_ids={tag_id},
            )
        )
        _, songs_total = get_songs_with_total_count(
            song_search_params=SongSearchParams(
                artist_ids=artist["id"],
                artist_participation_status="OnlyMainAlbums",
            )
        )
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
    return sorted_by_entry_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tag_id",
        type=int,
        help="Tag id to check.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger = get_logger("verify_artist_tags")

    table = get_tagged_artists_table(args.tag_id)
    logger.info(f"\nTag ({WEBSITE}/T/{args.tag_id}) - Most relevant artists:")
    logger.info(tabulate(table, headers="keys", tablefmt="github"))

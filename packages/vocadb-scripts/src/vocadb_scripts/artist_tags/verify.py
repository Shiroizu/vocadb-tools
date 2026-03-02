import argparse
from typing import Any

from tabulate import tabulate
from vdbpy.api.artists import get_artists_by_tag_id, get_song_count_by_artist_id_1d
from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger

MAX_ARTISTS = 50

logger = get_logger()


def get_tagged_artists_table(tag_id: int) -> tuple[list[Any], bool]:
    # TODO test
    artists_by_tag = get_artists_by_tag_id(tag_id)
    truncated = len(artists_by_tag) > MAX_ARTISTS
    logger.info(
        f"\nFound {len(artists_by_tag)} artists tagged with {WEBSITE}/T/{tag_id}"
    )
    if truncated:
        logger.warning("Only the first 50 artists will be included in the table")
    tagged_entry_counts: dict[str, Any] = {}

    for counter, artist in enumerate(artists_by_tag[:MAX_ARTISTS]):
        logger.info(f"Artist {counter}/{len(artists_by_tag)}")
        artist_id = artist["id"]
        tagged_song_count = get_song_count_by_artist_id_1d(
            artist_id, only_main_songs=True, extra_params={"tagId[]": tag_id}
        )
        songs_total = get_song_count_by_artist_id_1d(artist_id, only_main_songs=True)
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
    return sorted_by_entry_count, truncated


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

    table, truncated = get_tagged_artists_table(args.tag_id)
    logger.info(f"\nTag ({WEBSITE}/T/{args.tag_id}) - Most relevant artists:")
    if truncated:
        logger.warning(f"Results limited to first {MAX_ARTISTS} artists.")
    logger.info(tabulate(table, headers="keys", tablefmt="github"))

import argparse
from typing import Any

from tabulate import tabulate
from vdbpy.api.artists import get_artist_by_id_1d
from vdbpy.api.songs import SongSearchParams, get_songs_with_total_count
from vdbpy.utils.logger import get_logger

logger = get_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "artist_id",
        type=int,
        help="Artist id to check.",
    )
    parser.add_argument(
        "--only_with_pvs",
        help="Only include entries with PVs.",
        action="store_true",
    )
    parser.add_argument(
        "--include_collabs",
        help="Include entries where the artist is only participating.",
        action="store_true",
    )

    return parser.parse_args()


def get_artist_tag_table(
    artist_id: int,
    include_collabs: bool = False,
    only_with_pvs: bool = False,
    max_results: int = 0,
) -> tuple[list[Any], bool]:
    # TODO test
    songs_by_artist, total_count = get_songs_with_total_count(
        fields={"tags"},
        song_search_params=SongSearchParams(
            artist_ids={artist_id},
            artist_participation_status="Everything"
            if include_collabs
            else "OnlyMainAlbums",
            only_with_pvs=only_with_pvs,
            max_results=max_results,
        ),
    )
    truncated = bool(max_results and total_count > max_results)
    logger.info(f"\nFound {len(songs_by_artist)} songs")
    tag_counts: dict[Any, Any] = {}
    for song in songs_by_artist:
        assert song.tags != "Unknown"  # noqa: S101
        for tag in song.tags:
            if tag.tag_id not in tag_counts:
                tag_counts[tag.tag_id] = {
                    "entry_count": 1,
                    "name": tag.name,
                    "category": tag.category,
                    "tag_id": tag.tag_id,
                }
            else:
                tag_counts[tag.tag_id]["entry_count"] += 1

    artist_entry = get_artist_by_id_1d(artist_id, fields=["tags"])
    artist_entry_tag_ids = [tag["tag"]["id"] for tag in artist_entry["tags"]]
    tags_to_print = tag_counts.values()
    sorted_by_entry_count = sorted(
        tags_to_print, key=lambda x: x["entry_count"], reverse=True
    )
    for tag in sorted_by_entry_count:
        if tag["tag_id"] in artist_entry_tag_ids:
            tag["tag_added"] = True
        else:
            tag["tag_added"] = False
    return sorted_by_entry_count, truncated


if __name__ == "__main__":
    logger = get_logger("artist_tags_by_songs")
    args = parse_args()

    artist_name = get_artist_by_id_1d(args.artist_id)["name"]
    table, truncated = get_artist_tag_table(
        args.artist_id,
        include_collabs=args.include_collabs,
        only_with_pvs=args.only_with_pvs,
    )

    pvs_only = ", (pvs only)" if args.only_with_pvs else ""
    participation = "main songs" if not args.include_collabs else "including collabs"
    logger.info(
        f"\nArtist '{artist_name}' (Ar/{args.artist_id})"
        f" - Most common tags ({participation}){pvs_only}:"
    )
    if truncated:
        logger.warning("Results were truncated.")
    logger.info(tabulate(table, headers="keys", tablefmt="github"))

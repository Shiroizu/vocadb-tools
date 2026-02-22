"""Generate two graphs for rated & published songs by month by user id."""

import argparse
from datetime import UTC, datetime

from vdbpy.api.songs import OptionalSongFieldName, SongSearchParams, get_songs
from vdbpy.api.users import get_username_by_id
from vdbpy.utils.graph import generate_date_graph
from vdbpy.utils.logger import get_logger

logger = get_logger("monthly_rated_songs_by_user")


def get_months(start_year: int) -> list[str]:
    logger.debug(f"Fetching months from start year {start_year}")
    months: list[str] = []
    for year in range(start_year, datetime.now(tz=UTC).year + 1):
        for month in range(1, 13):
            month_string = f"{year:04}-{month:02}"
            months.append(month_string)
    return months


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "user_id",
        type=int,
        help="VocaDB user id",
    )

    return parser.parse_args()


def get_rated_songs_by_month_by_user_id(
    user_id: int,
) -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    # TODO test

    song_ids_by_published_month: dict[str, list[int]] = {}
    song_ids_by_rated_month: dict[str, list[int]] = {}

    fields: set[OptionalSongFieldName] = {
        "albums",
        "artists",
        "pvs",
        "releaseEvent",
        "tags",
        "webLinks",
        "cultureCodes",
    }

    rated_songs = get_songs(
        fields=fields, song_search_params=SongSearchParams(user_collection_id=user_id)
    )

    for song in rated_songs:
        if song.publish_date:
            year_and_month = str(song.publish_date)[:7]

            if year_and_month not in song_ids_by_published_month:
                song_ids_by_published_month[year_and_month] = []
                song_ids_by_published_month[year_and_month].append(song.id)

            if year_and_month not in song_ids_by_rated_month:
                song_ids_by_rated_month[year_and_month] = []
                song_ids_by_rated_month[year_and_month].append(song.id)
        else:
            logger.info(f"Song S/{song.id} has no publish date.")

    return song_ids_by_published_month, song_ids_by_rated_month


if __name__ == "__main__":
    args = parse_args()
    user_id = args.user_id
    username = get_username_by_id(user_id)
    logger.info(
        f"Generating a graph of monthly rated songs for user '{user_id}' ({username})"
    )

    song_ids_by_published_month, song_ids_by_rated_month = (
        get_rated_songs_by_month_by_user_id(user_id)
    )

    sp = [(str(month), len(ids)) for month, ids in song_ids_by_published_month.items()]
    title = f"{username}'s ({user_id}) rated songs by publish date"
    generate_date_graph(sp, title=title, date_format="%Y-%m")

    sr = [(str(month), len(ids)) for month, ids in song_ids_by_rated_month.items()]
    title = f"{username}'s ({user_id}) rated songs by rating date"
    generate_date_graph(sr, title=title, date_format="%Y-%m")

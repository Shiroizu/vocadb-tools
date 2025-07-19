"""Generate two graphs for rated & published songs by month by user id."""

import argparse
import datetime

from vdbpy.api.users import get_rated_songs_by_user_id, get_username_by_id
from vdbpy.utils.graph import generate_date_graph
from vdbpy.utils.logger import get_logger

logger = get_logger("monthly_rated_songs_by_user")


def get_months(start_year: int) -> list[str]:
    logger.debug(f"Fetching months from start year {start_year}")
    months: list[str] = []
    for year in range(start_year, datetime.datetime.now().year + 1):
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


if __name__ == "__main__":
    args = parse_args()
    user_id = args.user_id
    username = get_username_by_id(user_id)
    logger.info(
        f"Generating a graph of monthly rated songs for user '{user_id}' ({username})"
    )

    song_ids_by_published_month = {}
    song_ids_by_rated_month = {}

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

    for song in rated_songs:
        song_id = song["song"]["id"]
        if "publishDate" in song["song"]:
            # "2013-04-26T00:00:00Z"
            year_and_month = song["song"]["publishDate"][:7]

            if year_and_month not in song_ids_by_published_month:
                song_ids_by_published_month[year_and_month] = []
            song_ids_by_published_month[year_and_month].append(song_id)
        else:
            logger.info(f"Song S/{song_id} has no publish date.")

        year_and_month = song["date"][:7]
        if year_and_month not in song_ids_by_rated_month:
            song_ids_by_rated_month[year_and_month] = []
        song_ids_by_rated_month[year_and_month].append(song_id)

    sp = [(str(month), len(ids)) for month, ids in song_ids_by_published_month.items()]
    title = f"{username}'s ({user_id}) rated songs by publish date"
    generate_date_graph(sp, title=title, date_format="%Y-%m")

    sr = [(str(month), len(ids)) for month, ids in song_ids_by_rated_month.items()]
    title = f"{username}'s ({user_id}) rated songs by rating date"
    generate_date_graph(sr, title=title, date_format="%Y-%m")

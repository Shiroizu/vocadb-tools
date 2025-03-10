"""Generate two graphs for rated & published songs by month by user id."""

import datetime
import sys

from api.users import get_rated_songs
from utils.console import get_parameter
from utils.graph import generate_date_graph

user_id = int(get_parameter("VocaDB user id: ", sys.argv, integer=True))


def get_months(start_year: int) -> list[str]:
    months: list[str] = []
    for year in range(start_year, datetime.datetime.now().year + 1):
        for month in range(1, 13):
            month_string = f"{year:04}-{month:02}"
            months.append(month_string)
    return months


song_ids_by_published_month = {}
song_ids_by_rated_month = {}

rated_songs = get_rated_songs(user_id)

for song in rated_songs:
    song_id = song["song"]["id"]
    if "publishDate" in song["song"]:
        # "2013-04-26T00:00:00Z"
        year_and_month = song["song"]["publishDate"][:7]

        if year_and_month not in song_ids_by_published_month:
            song_ids_by_published_month[year_and_month] = []
        song_ids_by_published_month[year_and_month].append(song_id)
    else:
        print(f"Song S/{song_id} has no publish date.")

    year_and_month = song["date"][:7]
    if year_and_month not in song_ids_by_rated_month:
        song_ids_by_rated_month[year_and_month] = []
    song_ids_by_rated_month[year_and_month].append(song_id)


sp = [(str(month), len(ids)) for month, ids in song_ids_by_published_month.items()]
generate_date_graph(sp, title="Rated songs by publish date", date_format="%Y-%m")

sr = [(str(month), len(ids)) for month, ids in song_ids_by_rated_month.items()]
generate_date_graph(sr, title="Song rated by month", date_format="%Y-%m")

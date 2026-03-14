"""Rated songs by publish month graph."""

import sys
from datetime import UTC, datetime

import plotly.graph_objects as go
from vdbpy.api.songs import get_cached_rated_songs_with_ratings
from vdbpy.utils.logger import get_logger

logger = get_logger()


def _collect(
    user_id: int, username: str
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    logger.info(f"Generating rated songs graph for '{username}' ({user_id})")
    rated_songs = get_cached_rated_songs_with_ratings(user_id)
    by_publish: dict[str, int] = {}
    by_rating: dict[str, int] = {}
    for entry in rated_songs:
        song = entry["song"]
        publish_date = song.get("publishDate")
        if publish_date:
            month = publish_date[:7]
            by_publish[month] = by_publish.get(month, 0) + 1
        else:
            logger.info(f"Song S/{song['id']} has no publish date.")
        rating_date = entry.get("date")
        if rating_date:
            month = rating_date[:7]
            by_rating[month] = by_rating.get(month, 0) + 1
    return sorted(by_publish.items()), sorted(by_rating.items())


def _to_xy(data: list[tuple[str, int]]) -> tuple[list[datetime], list[int]]:
    dates = [datetime.strptime(d, "%Y-%m").replace(tzinfo=UTC) for d, _ in data]
    values = [v for _, v in data]
    return dates, values


def _figure(user_id: int, username: str) -> go.Figure:
    publish_data, rating_data = _collect(user_id, username)
    pub_dates, pub_values = _to_xy(publish_data)
    rat_dates, rat_values = _to_xy(rating_data)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=pub_dates, y=pub_values, mode="lines+markers", name="Publish date")
    )
    fig.add_trace(
        go.Scatter(x=rat_dates, y=rat_values, mode="lines+markers", name="Rating date")
    )
    fig.update_layout(
        title=f"{username}'s rated songs by month",
        xaxis_title="Month",
        yaxis_title="Songs",
        xaxis={"tickformat": "%Y-%m"},
    )
    return fig


def get_rated_songs_png(user_id: int, username: str) -> bytes:
    """Return PNG of rated songs grouped by publish month for the given user."""
    return _figure(user_id, username).to_image(format="png")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(f"Usage: {sys.argv[0]} <user_id> <username>")
    _figure(int(sys.argv[1]), sys.argv[2]).show()
